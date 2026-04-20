#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray, String


class CmdvelToRf1:
    def __init__(self):
        self.wb_m = float(rospy.get_param("~wb_m", 0.1905))
        self.tw_m = float(rospy.get_param("~tw_m", 0.1800))
        self.k_m = float(rospy.get_param("~k_m", 0.18525))
        self.publish_rate_hz = float(rospy.get_param("~publish_rate_hz", 50.0))
        self.cmd_vel_timeout = float(rospy.get_param("~cmd_vel_timeout", 0.4))
        self.max_vx = float(rospy.get_param("~max_vx", 0.20))
        self.max_vy = float(rospy.get_param("~max_vy", 0.15))
        self.max_wz = float(rospy.get_param("~max_wz", 0.35))

        self.last_cmd = Twist()
        self.last_cmd_time = None

        self.pub = rospy.Publisher("/rf1/wheel_target_ms", Float32MultiArray, queue_size=20)
        self.status_pub = rospy.Publisher("/rf1/cmdvel_status", String, queue_size=20, latch=True)
        self.debug_pub = rospy.Publisher("/rf1/cmdvel_debug", String, queue_size=20)

        rospy.Subscriber("/cmd_vel", Twist, self.cmd_vel_callback, queue_size=20)
        self.status_pub.publish(String(data="cmdvel_to_rf1 ready"))

    def cmd_vel_callback(self, msg):
        self.last_cmd = msg
        self.last_cmd_time = rospy.Time.now()

    def current_command(self):
        if self.last_cmd_time is None:
            return 0.0, 0.0, 0.0

        age = (rospy.Time.now() - self.last_cmd_time).to_sec()
        if age > self.cmd_vel_timeout:
            return 0.0, 0.0, 0.0

        return (
            self.clamp(self.last_cmd.linear.x, -self.max_vx, self.max_vx),
            self.clamp(self.last_cmd.linear.y, -self.max_vy, self.max_vy),
            self.clamp(self.last_cmd.angular.z, -self.max_wz, self.max_wz),
        )

    def clamp(self, value, lower, upper):
        if value < lower:
            return lower
        if value > upper:
            return upper
        return value

    def convert_cmd_vel(self, vx, vy, wz):
        return [
            vx - vy - self.k_m * wz,
            vx + vy + self.k_m * wz,
            vx + vy - self.k_m * wz,
            vx - vy + self.k_m * wz,
        ]

    def publish_debug(self, vx, vy, wz, targets):
        self.debug_pub.publish(
            String(
                data=(
                    f"cmd_vel vx={vx:.3f} vy={vy:.3f} wz={wz:.3f} "
                    f"targets={[round(value, 3) for value in targets]}"
                )
            )
        )

    def spin(self):
        rate = rospy.Rate(self.publish_rate_hz)
        while not rospy.is_shutdown():
            vx, vy, wz = self.current_command()
            targets = self.convert_cmd_vel(vx, vy, wz)
            self.pub.publish(Float32MultiArray(data=targets))
            self.publish_debug(vx, vy, wz, targets)
            rate.sleep()


def main():
    rospy.init_node("cmdvel_to_rf1")
    CmdvelToRf1().spin()


if __name__ == "__main__":
    main()
