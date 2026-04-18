#!/usr/bin/env python3

import math

import rospy
import smbus
from geometry_msgs.msg import Vector3
from sensor_msgs.msg import Imu


class Mpu6050Node:
    def __init__(self):
        self.bus = int(rospy.get_param("~bus", 1))
        self.address = int(rospy.get_param("~address", 0x68))
        self.frame_id = rospy.get_param("~frame_id", "imu_link")
        self.rate_hz = float(rospy.get_param("~rate_hz", 50.0))
        self.accel_scale = float(rospy.get_param("~accel_scale", 16384.0))
        self.gyro_scale = float(rospy.get_param("~gyro_scale", 131.0))
        self.bus_handle = smbus.SMBus(self.bus)

        self.raw_pub = rospy.Publisher("/imu/data", Imu, queue_size=50)

        self.write_register(0x6B, 0x00)
        self.write_register(0x1C, 0x00)
        self.write_register(0x1B, 0x00)

    def write_register(self, register, value):
        self.bus_handle.write_byte_data(self.address, register, value)

    def read_word_signed(self, register):
        high = self.bus_handle.read_byte_data(self.address, register)
        low = self.bus_handle.read_byte_data(self.address, register + 1)
        value = (high << 8) | low
        if value >= 0x8000:
            value -= 0x10000
        return value

    def read_measurements(self):
        accel_x = self.read_word_signed(0x3B)
        accel_y = self.read_word_signed(0x3D)
        accel_z = self.read_word_signed(0x3F)
        gyro_x = self.read_word_signed(0x43)
        gyro_y = self.read_word_signed(0x45)
        gyro_z = self.read_word_signed(0x47)
        return accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z

    def publish_once(self):
        accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = self.read_measurements()

        msg = Imu()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = self.frame_id
        msg.linear_acceleration = Vector3(
            x=(accel_x / self.accel_scale) * 9.80665,
            y=(accel_y / self.accel_scale) * 9.80665,
            z=(accel_z / self.accel_scale) * 9.80665,
        )
        msg.angular_velocity = Vector3(
            x=math.radians(gyro_x / self.gyro_scale),
            y=math.radians(gyro_y / self.gyro_scale),
            z=math.radians(gyro_z / self.gyro_scale),
        )
        msg.orientation_covariance[0] = -1.0
        msg.angular_velocity_covariance[0] = 0.02
        msg.angular_velocity_covariance[4] = 0.02
        msg.angular_velocity_covariance[8] = 0.02
        msg.linear_acceleration_covariance[0] = 0.04
        msg.linear_acceleration_covariance[4] = 0.04
        msg.linear_acceleration_covariance[8] = 0.04

        self.raw_pub.publish(msg)

    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            try:
                self.publish_once()
            except OSError as exc:
                rospy.logerr_throttle(2.0, "mpu6050 i2c access failed: %s", str(exc))
            rate.sleep()


def main():
    rospy.init_node("mpu6050_i2c_node")
    node = Mpu6050Node()
    node.spin()


if __name__ == "__main__":
    main()
