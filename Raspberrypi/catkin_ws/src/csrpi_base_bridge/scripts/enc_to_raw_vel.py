#!/usr/bin/env python3

import rospy
from clb_msgs.msg import Velocities
from std_msgs.msg import Float32MultiArray


class EncoderToRawVel:
    def __init__(self):
        self.radius = float(rospy.get_param("~wheel_radius_m", 0.039))
        self.k_m = float(rospy.get_param("~k_m", 0.171925))
        self.scale = float(rospy.get_param("~ticks_scale", 1.0))
        self.pub = rospy.Publisher("raw_vel", Velocities, queue_size=20)
        rospy.Subscriber("/csr_base/encoder_debug", Float32MultiArray, self.callback, queue_size=20)

    def callback(self, msg):
        data = list(msg.data)
        if len(data) < 8:
            return

        v1, v2, v3, v4 = [value * self.scale for value in data[4:8]]

        out = Velocities()
        out.linear_x = self.radius * (v1 + v2 + v3 + v4) / 4.0
        out.linear_y = self.radius * (-v1 + v2 + v3 - v4) / 4.0
        out.angular_z = self.radius * (-v1 + v2 - v3 + v4) / (4.0 * self.k_m)
        self.pub.publish(out)


def main():
    rospy.init_node("csrpi_enc_to_raw_vel")
    EncoderToRawVel()
    rospy.spin()


if __name__ == "__main__":
    main()
