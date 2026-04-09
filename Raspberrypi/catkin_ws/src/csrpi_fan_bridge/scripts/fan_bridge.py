#!/usr/bin/env python3

import pigpio
import rospy
from std_msgs.msg import Bool, Float32


class FanBridge:
    def __init__(self):
        self.relay_gpio = int(rospy.get_param("~relay_gpio", 17))
        self.pwm_gpio = int(rospy.get_param("~pwm_gpio", 18))
        self.pwm_freq_hz = int(rospy.get_param("~pwm_freq_hz", 25000))
        self.enable_delay = float(rospy.get_param("~enable_delay", 0.2))
        self.enabled = False
        self.last_percent = 0.0

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemon is not running")

        self.pi.set_mode(self.relay_gpio, pigpio.OUTPUT)
        self.pi.write(self.relay_gpio, 0)
        self.pi.hardware_PWM(self.pwm_gpio, self.pwm_freq_hz, 0)

        rospy.Subscriber("/fan_enable", Bool, self.enable_callback, queue_size=10)
        rospy.Subscriber("/fan_pwm_percent", Float32, self.percent_callback, queue_size=10)

    def set_pwm_percent(self, percent):
        percent = max(0.0, min(100.0, percent))
        duty = int(percent * 10000)
        self.pi.hardware_PWM(self.pwm_gpio, self.pwm_freq_hz, duty)
        self.last_percent = percent

    def enable_callback(self, msg):
        if msg.data and not self.enabled:
            self.pi.write(self.relay_gpio, 1)
            rospy.sleep(self.enable_delay)
            self.set_pwm_percent(self.last_percent)
            self.enabled = True
        elif not msg.data and self.enabled:
            self.set_pwm_percent(0.0)
            rospy.sleep(0.2)
            self.pi.write(self.relay_gpio, 0)
            self.enabled = False

    def percent_callback(self, msg):
        self.last_percent = max(0.0, min(100.0, msg.data))
        if self.enabled:
            self.set_pwm_percent(self.last_percent)


def main():
    rospy.init_node("csrpi_fan_bridge")
    FanBridge()
    rospy.spin()


if __name__ == "__main__":
    main()
