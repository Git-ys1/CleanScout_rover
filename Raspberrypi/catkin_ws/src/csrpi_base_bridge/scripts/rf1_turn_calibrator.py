#!/usr/bin/env python3

import json
import math
import statistics
import sys
import time

import rospy
from geometry_msgs.msg import Pose2D, Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32MultiArray


class TrapezoidIntegrator:
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = 0.0
        self.last_stamp = None
        self.last_sample = None
        self.samples = 0

    def add(self, stamp, sample):
        if self.last_stamp is not None:
            dt = stamp - self.last_stamp
            if 0.0 < dt < 0.5:
                self.value += 0.5 * (self.last_sample + sample) * dt
        self.last_stamp = stamp
        self.last_sample = sample
        self.samples += 1


class Rf1TurnCalibrator:
    def __init__(self):
        self.command_topic = rospy.get_param("~command_topic", "/cmd_vel_nav")
        self.wheel_topic = rospy.get_param("~wheel_topic", "/rf1/vel")
        self.imu_topic = rospy.get_param("~imu_topic", "/imu/data_raw")
        self.pose_topic = rospy.get_param("~pose_topic", "/pose2D_turn_calib")
        self.odom_topic = rospy.get_param("~odom_topic", "/odom")
        self.direction = int(rospy.get_param("~direction", 1))
        self.command_wz = abs(float(rospy.get_param("~command_wz", 0.20)))
        self.turn_sec = float(rospy.get_param("~turn_sec", 3.0))
        self.bias_sec = float(rospy.get_param("~bias_sec", 3.0))
        self.settle_sec = float(rospy.get_param("~settle_sec", 1.5))
        self.sensor_timeout = float(rospy.get_param("~sensor_timeout", 8.0))
        self.stationary_wheel_limit = float(
            rospy.get_param("~stationary_wheel_limit", 0.03)
        )
        self.output_path = rospy.get_param("~output", "")

        if self.direction not in (-1, 1):
            raise ValueError("~direction must be -1 (right) or 1 (left)")
        if self.command_wz <= 0.0 or self.turn_sec <= 0.0:
            raise ValueError("~command_wz and ~turn_sec must be positive")

        self.command_pub = rospy.Publisher(
            self.command_topic, Twist, queue_size=20
        )
        self.latest_wheels = None
        self.latest_imu_z = None
        self.latest_pose_theta = None
        self.pose_unwrapped = None
        self.pose_previous = None
        self.odom_unwrapped = None
        self.odom_previous = None
        self.imu_bias_samples = []
        self.stationary_wheel_max = 0.0
        self.recording = False

        self.wheel_integrator = TrapezoidIntegrator()
        self.imu_integrator = TrapezoidIntegrator()
        self.pose_start = None
        self.odom_start = None
        self.wheel_sample_sums = [0.0] * 4
        self.wheel_sample_count = 0

        rospy.Subscriber(
            self.wheel_topic, Float32MultiArray, self.wheel_callback, queue_size=100
        )
        rospy.Subscriber(self.imu_topic, Imu, self.imu_callback, queue_size=200)
        rospy.Subscriber(self.pose_topic, Pose2D, self.pose_callback, queue_size=50)
        rospy.Subscriber(self.odom_topic, Odometry, self.odom_callback, queue_size=100)
        rospy.on_shutdown(self.publish_stop)

    @staticmethod
    def message_stamp(msg):
        if hasattr(msg, "header") and msg.header.stamp != rospy.Time():
            return msg.header.stamp.to_sec()
        return rospy.Time.now().to_sec()

    def wheel_callback(self, msg):
        if len(msg.data) < 4:
            return
        wheels = [float(value) for value in msg.data[:4]]
        self.latest_wheels = wheels

        if self.imu_bias_samples is not None and not self.recording:
            self.stationary_wheel_max = max(
                self.stationary_wheel_max, max(abs(value) for value in wheels)
            )

        if not self.recording:
            return

        lr, lf, rr, rf = wheels
        rotational_numerator = (-lr - lf + rr + rf) / 4.0
        self.wheel_integrator.add(rospy.Time.now().to_sec(), rotational_numerator)
        for index, value in enumerate(wheels):
            self.wheel_sample_sums[index] += value
        self.wheel_sample_count += 1

    def imu_callback(self, msg):
        self.latest_imu_z = float(msg.angular_velocity.z)
        if self.imu_bias_samples is not None and not self.recording:
            self.imu_bias_samples.append(self.latest_imu_z)
        if self.recording:
            corrected_z = self.latest_imu_z - self.imu_bias
            self.imu_integrator.add(self.message_stamp(msg), corrected_z)

    def pose_callback(self, msg):
        theta = float(msg.theta)
        self.latest_pose_theta = theta
        if self.pose_previous is None:
            self.pose_previous = theta
            self.pose_unwrapped = theta
            return

        delta = math.atan2(
            math.sin(theta - self.pose_previous),
            math.cos(theta - self.pose_previous),
        )
        self.pose_unwrapped += delta
        self.pose_previous = theta

    def odom_callback(self, msg):
        quat = msg.pose.pose.orientation
        theta = math.atan2(
            2.0 * (quat.w * quat.z + quat.x * quat.y),
            1.0 - 2.0 * (quat.y * quat.y + quat.z * quat.z),
        )
        if self.odom_previous is None:
            self.odom_previous = theta
            self.odom_unwrapped = theta
            return

        delta = math.atan2(
            math.sin(theta - self.odom_previous),
            math.cos(theta - self.odom_previous),
        )
        self.odom_unwrapped += delta
        self.odom_previous = theta

    def publish_command(self, angular_z):
        cmd = Twist()
        cmd.angular.z = angular_z
        self.command_pub.publish(cmd)

    def publish_stop(self):
        if not hasattr(self, "command_pub"):
            return
        stop = Twist()
        for _ in range(12):
            self.command_pub.publish(stop)
            time.sleep(0.025)

    def wait_for_sensors(self):
        deadline = time.monotonic() + self.sensor_timeout
        rate = rospy.Rate(20)
        while not rospy.is_shutdown():
            if (
                self.latest_wheels is not None
                and self.latest_imu_z is not None
                and self.pose_unwrapped is not None
                and self.command_pub.get_num_connections() > 0
            ):
                return
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "sensor timeout: wheels=%s imu=%s lidar_pose=%s command_subscribers=%d"
                    % (
                        self.latest_wheels is not None,
                        self.latest_imu_z is not None,
                        self.pose_unwrapped is not None,
                        self.command_pub.get_num_connections(),
                    )
                )
            self.publish_command(0.0)
            rate.sleep()

    def collect_bias(self):
        self.imu_bias_samples = []
        self.stationary_wheel_max = 0.0
        deadline = time.monotonic() + self.bias_sec
        rate = rospy.Rate(20)
        while not rospy.is_shutdown() and time.monotonic() < deadline:
            self.publish_command(0.0)
            rate.sleep()

        if len(self.imu_bias_samples) < 20:
            raise RuntimeError("not enough IMU samples for bias estimation")
        if self.stationary_wheel_max > self.stationary_wheel_limit:
            raise RuntimeError(
                "robot was not stationary during bias collection: max wheel %.4f m/s"
                % self.stationary_wheel_max
            )

        self.imu_bias = statistics.mean(self.imu_bias_samples)
        self.imu_bias_std = statistics.stdev(self.imu_bias_samples)
        self.imu_bias_samples = None

    def reset_recording(self):
        self.wheel_integrator.reset()
        self.imu_integrator.reset()
        self.wheel_sample_sums = [0.0] * 4
        self.wheel_sample_count = 0
        self.pose_start = self.pose_unwrapped
        self.odom_start = self.odom_unwrapped
        self.recording = True

    def run_motion(self):
        self.reset_recording()
        rate = rospy.Rate(30)
        angular_z = self.direction * self.command_wz
        motion_end = time.monotonic() + self.turn_sec
        while not rospy.is_shutdown() and time.monotonic() < motion_end:
            self.publish_command(angular_z)
            rate.sleep()

        settle_end = time.monotonic() + self.settle_sec
        while not rospy.is_shutdown() and time.monotonic() < settle_end:
            self.publish_command(0.0)
            rate.sleep()
        self.recording = False
        self.publish_stop()

    @staticmethod
    def estimate_k(wheel_integral, angle):
        if abs(angle) < math.radians(10.0):
            return None
        return wheel_integral / angle

    def build_result(self):
        wheel_integral = self.wheel_integrator.value
        imu_angle = self.imu_integrator.value
        lidar_angle = self.pose_unwrapped - self.pose_start
        odom_angle = None
        if self.odom_start is not None and self.odom_unwrapped is not None:
            odom_angle = self.odom_unwrapped - self.odom_start
        wheel_means = [
            value / self.wheel_sample_count
            for value in self.wheel_sample_sums
        ]
        k_imu = self.estimate_k(wheel_integral, imu_angle)
        k_lidar = self.estimate_k(wheel_integral, lidar_angle)

        result = {
            "direction": "left" if self.direction > 0 else "right",
            "command_wz_rad_s": self.direction * self.command_wz,
            "turn_sec": self.turn_sec,
            "imu_bias_rad_s": self.imu_bias,
            "imu_bias_std_rad_s": self.imu_bias_std,
            "stationary_wheel_max_m_s": self.stationary_wheel_max,
            "wheel_integral_m": wheel_integral,
            "imu_angle_rad": imu_angle,
            "imu_angle_deg": math.degrees(imu_angle),
            "lidar_angle_rad": lidar_angle,
            "lidar_angle_deg": math.degrees(lidar_angle),
            "odom_angle_rad": odom_angle,
            "odom_angle_deg": (
                math.degrees(odom_angle) if odom_angle is not None else None
            ),
            "odom_lidar_disagreement_deg": (
                math.degrees(odom_angle - lidar_angle)
                if odom_angle is not None
                else None
            ),
            "imu_lidar_disagreement_deg": math.degrees(imu_angle - lidar_angle),
            "k_from_imu_m": k_imu,
            "k_from_lidar_m": k_lidar,
            "wheel_mean_m_s_lr_lf_rr_rf": wheel_means,
            "wheel_samples": self.wheel_integrator.samples,
            "imu_samples": self.imu_integrator.samples,
        }
        return result

    def run(self):
        rospy.loginfo("Waiting for RF1, IMU, lidar matcher, and command gate")
        self.wait_for_sensors()
        rospy.loginfo("Collecting %.1f seconds of stationary IMU bias", self.bias_sec)
        self.collect_bias()
        rospy.loginfo(
            "IMU z bias %.6f rad/s (std %.6f); starting %s turn",
            self.imu_bias,
            self.imu_bias_std,
            "left" if self.direction > 0 else "right",
        )
        self.run_motion()
        result = self.build_result()

        payload = json.dumps(result, sort_keys=True, indent=2)
        print("RF1_TURN_CALIBRATION_RESULT")
        print(payload)
        if self.output_path:
            with open(self.output_path, "w", encoding="utf-8") as output_file:
                output_file.write(payload)
                output_file.write("\n")
        return result


def main():
    rospy.init_node("rf1_turn_calibrator")
    calibrator = None
    try:
        calibrator = Rf1TurnCalibrator()
        result = calibrator.run()
        if result["k_from_imu_m"] is None or result["k_from_lidar_m"] is None:
            raise RuntimeError("turn angle was too small for a reliable estimate")
    except Exception as exc:
        if calibrator is not None:
            calibrator.publish_stop()
        rospy.logerr("RF1 turn calibration failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
