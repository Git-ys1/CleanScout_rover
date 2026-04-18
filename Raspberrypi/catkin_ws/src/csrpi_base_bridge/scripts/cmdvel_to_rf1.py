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
        self.cmd_vel_timeout = float(rospy.get_param("~cmd_vel_timeout", 0.25))

        self.last_cmd = Twist()
        self.last_cmd_time = None

        self.pub = rospy.Publisher("/rf1/wheel_target_ms", Float32MultiArray, queue_size=20)
        self.status_pub = rospy.Publisher("/rf1/cmdvel_status", String, queue_size=20, latch=True)

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

        return self.last_cmd.linear.x, self.last_cmd.linear.y, self.last_cmd.angular.z

    def convert_cmd_vel(self, vx, vy, wz):
        return [
            vx - vy - self.k_m * wz,
            vx + vy + self.k_m * wz,
            vx + vy - self.k_m * wz,
            vx - vy + self.k_m * wz,
        ]

    def spin(self):
        rate = rospy.Rate(self.publish_rate_hz)
        while not rospy.is_shutdown():
            vx, vy, wz = self.current_command()
            targets = self.convert_cmd_vel(vx, vy, wz)
            self.pub.publish(Float32MultiArray(data=targets))
            rate.sleep()


def main():
    rospy.init_node("cmdvel_to_rf1")
    CmdvelToRf1().spin()


if __name__ == "__main__":
    main()
