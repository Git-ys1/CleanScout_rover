#!/usr/bin/env python3

import math

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32MultiArray, String


class CmdvelToWheels:
    def __init__(self):
        self.d_eff_m = float(rospy.get_param("~d_eff_m", 0.078))
        self.wb_m = float(rospy.get_param("~wb_m", 0.16535))
        self.tw_m = float(rospy.get_param("~tw_m", 0.17850))
        self.k_m = float(rospy.get_param("~k_m", 0.171925))
        self.cpr_x1_est = float(rospy.get_param("~cpr_x1_est", 260.0))
        self.min_abs_ticks = int(rospy.get_param("~min_abs_ticks", 300))
        self.enabled = bool(rospy.get_param("~enabled", False))

        self.pub = rospy.Publisher("/csr_base/wheel_targets", Int32MultiArray, queue_size=20)
        self.status_pub = rospy.Publisher("/csr_base/cmdvel_converter_status", String, queue_size=20, latch=True)

        rospy.Subscriber("/cmd_vel", Twist, self.cmd_vel_callback, queue_size=20)
        self.status_pub.publish(String(data=f"cmdvel_to_wheels enabled={self.enabled}"))

    def cmd_vel_callback(self, msg):
        if not self.enabled:
            return

        targets = self.convert_cmd_vel(msg.linear.x, msg.linear.y, msg.angular.z)
        self.pub.publish(Int32MultiArray(data=targets))

    def convert_cmd_vel(self, vx, vy, wz):
        radius = self.d_eff_m / 2.0
        if radius <= 0.0:
            rospy.logwarn_throttle(2.0, "invalid effective wheel diameter")
            return [0, 0, 0, 0]

        wheel_rad_s = [
            (vx - vy - self.k_m * wz) / radius,
            (vx + vy + self.k_m * wz) / radius,
            (vx + vy - self.k_m * wz) / radius,
            (vx - vy + self.k_m * wz) / radius,
        ]

        ticks_per_sec = []
        for value in wheel_rad_s:
            rev_per_sec = value / (2.0 * math.pi)
            ticks = int(round(rev_per_sec * self.cpr_x1_est))
            if ticks != 0 and abs(ticks) < self.min_abs_ticks:
                ticks = self.min_abs_ticks if ticks > 0 else -self.min_abs_ticks
            ticks_per_sec.append(ticks)
        return ticks_per_sec


def main():
    rospy.init_node("csrpi_cmdvel_to_wheels")
    CmdvelToWheels()
    rospy.spin()


if __name__ == "__main__":
    main()
