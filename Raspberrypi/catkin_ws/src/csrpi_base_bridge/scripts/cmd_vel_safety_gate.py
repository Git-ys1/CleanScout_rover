#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist


class CmdVelSafetyGate:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/cmd_vel_nav")
        self.output_topic = rospy.get_param("~output_topic", "/cmd_vel")
        self.timeout = float(rospy.get_param("~timeout", 0.4))
        self.rate_hz = float(rospy.get_param("~rate", 30.0))
        self.min_vx = float(rospy.get_param("~min_vx", 0.0))
        self.max_vx = float(rospy.get_param("~max_vx", 0.20))
        self.max_vy = float(rospy.get_param("~max_vy", 0.15))
        self.max_wz = float(rospy.get_param("~max_wz", 0.35))
        self.allow_lateral = bool(rospy.get_param("~allow_lateral", True))

        if self.min_vx > 0.0 or self.min_vx > self.max_vx:
            raise ValueError("~min_vx must be <= 0 and <= ~max_vx")
        if self.max_vx < 0.0 or self.max_vy < 0.0 or self.max_wz < 0.0:
            raise ValueError("velocity limits must be non-negative")

        self.last_cmd = Twist()
        self.last_cmd_time = None

        self.pub = rospy.Publisher(self.output_topic, Twist, queue_size=20)
        rospy.Subscriber(self.input_topic, Twist, self.cmd_callback, queue_size=20)
        rospy.on_shutdown(self.publish_stop)

    def cmd_callback(self, msg):
        self.last_cmd = msg
        self.last_cmd_time = rospy.Time.now()

    @staticmethod
    def clamp(value, limit):
        return max(-limit, min(limit, value))

    @staticmethod
    def clamp_range(value, lower, upper):
        return max(lower, min(upper, value))

    def apply_limits(self, source):
        cmd = Twist()
        cmd.linear.x = self.clamp_range(
            source.linear.x, self.min_vx, self.max_vx
        )
        lateral_limit = self.max_vy if self.allow_lateral else 0.0
        cmd.linear.y = self.clamp(source.linear.y, lateral_limit)
        cmd.angular.z = self.clamp(source.angular.z, self.max_wz)
        return cmd

    def zero_twist(self):
        return Twist()

    def current_cmd(self):
        if self.last_cmd_time is None:
            return self.zero_twist()

        age = (rospy.Time.now() - self.last_cmd_time).to_sec()
        if age > self.timeout:
            return self.zero_twist()

        return self.apply_limits(self.last_cmd)

    def publish_stop(self):
        self.pub.publish(self.zero_twist())

    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            self.pub.publish(self.current_cmd())
            rate.sleep()


def main():
    rospy.init_node("cmd_vel_safety_gate")
    CmdVelSafetyGate().spin()


if __name__ == "__main__":
    main()
