#!/usr/bin/env python3

import math

import rospy
from sensor_msgs.msg import LaserScan


class ScanContractStub:
    def __init__(self):
        self.frame_id = rospy.get_param("~frame_id", "laser")
        self.rate_hz = float(rospy.get_param("~rate_hz", 5.0))
        self.range_max = float(rospy.get_param("~range_max", 12.0))
        self.pub = rospy.Publisher("/scan", LaserScan, queue_size=5)

    def build_msg(self):
        msg = LaserScan()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = self.frame_id
        msg.angle_min = -math.pi
        msg.angle_max = math.pi
        msg.angle_increment = math.radians(1.0)
        msg.time_increment = 0.0
        msg.scan_time = 1.0 / self.rate_hz if self.rate_hz > 0.0 else 0.2
        msg.range_min = 0.15
        msg.range_max = self.range_max
        count = int(round((msg.angle_max - msg.angle_min) / msg.angle_increment)) + 1
        msg.ranges = [float("inf")] * count
        msg.intensities = [0.0] * count
        return msg

    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            self.pub.publish(self.build_msg())
            rate.sleep()


def main():
    rospy.init_node("scan_contract_stub")
    ScanContractStub().spin()


if __name__ == "__main__":
    main()
