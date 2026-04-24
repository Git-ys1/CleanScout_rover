#!/usr/bin/env python3

import math

import rospy
import tf.transformations
from geometry_msgs.msg import Quaternion, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray
from tf2_ros import TransformBroadcaster


class Rf1VelToOdom:
    def __init__(self):
        self.k_m = float(rospy.get_param("~k_m", 0.18525))
        self.odom_frame = rospy.get_param("~odom_frame", "odom")
        self.base_frame = rospy.get_param("~base_frame", "base_link")
        self.publish_tf = bool(rospy.get_param("~publish_tf", False))
        self.base_yaw_offset = float(rospy.get_param("~base_yaw_offset", 0.0))

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_time = None

        self.odom_pub = rospy.Publisher("/odom", Odometry, queue_size=20)
        self.tf_pub = TransformBroadcaster() if self.publish_tf else None
        rospy.Subscriber("/rf1/vel", Float32MultiArray, self.callback, queue_size=20)

    def callback(self, msg):
        data = list(msg.data)
        if len(data) < 4:
            return

        v1, v2, v3, v4 = data[:4]
        vx = (v1 + v2 + v3 + v4) / 4.0
        vy = (-v1 + v2 + v3 - v4) / 4.0
        wz = (-v1 + v2 - v3 + v4) / (4.0 * self.k_m) if self.k_m else 0.0

        now = rospy.Time.now()
        if self.last_time is None:
            self.last_time = now
            self.publish_odom(now, vx, vy, wz)
            return

        dt = (now - self.last_time).to_sec()
        self.last_time = now
        if dt < 0.0:
            dt = 0.0

        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        self.x += (vx * cos_yaw - vy * sin_yaw) * dt
        self.y += (vx * sin_yaw + vy * cos_yaw) * dt
        self.yaw += wz * dt

        self.publish_odom(now, vx, vy, wz)

    def publish_odom(self, stamp, vx, vy, wz):
        odom_yaw = self.yaw + self.base_yaw_offset
        quat = tf.transformations.quaternion_from_euler(0.0, 0.0, odom_yaw)

        msg = Odometry()
        msg.header.stamp = stamp
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = self.base_frame
        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.orientation = Quaternion(*quat)
        msg.twist.twist.linear.x = vx
        msg.twist.twist.linear.y = vy
        msg.twist.twist.angular.z = wz
        self.odom_pub.publish(msg)

        if self.tf_pub is not None:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = stamp
            tf_msg.header.frame_id = self.odom_frame
            tf_msg.child_frame_id = self.base_frame
            tf_msg.transform.translation.x = self.x
            tf_msg.transform.translation.y = self.y
            tf_msg.transform.rotation = Quaternion(*quat)
            self.tf_pub.sendTransform(tf_msg)


def main():
    rospy.init_node("rf1_vel_to_odom")
    Rf1VelToOdom()
    rospy.spin()


if __name__ == "__main__":
    main()
