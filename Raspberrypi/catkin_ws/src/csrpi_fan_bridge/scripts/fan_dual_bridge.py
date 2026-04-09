#!/usr/bin/env python3

import RPi.GPIO as GPIO
import rospy
from std_msgs.msg import Bool, Float32


class FanDualBridge:
    def __init__(self):
        self.relay_gpio = int(rospy.get_param("~relay_gpio", 17))
        self.fan_a_gpio = int(rospy.get_param("~fan_a_gpio", 18))
        self.fan_b_gpio = int(rospy.get_param("~fan_b_gpio", 19))
        self.pwm_freq_hz = int(rospy.get_param("~pwm_freq_hz", 25000))
        self.enable_delay = float(rospy.get_param("~enable_delay", 0.2))
        self.enabled = False
        self.fan_a_percent = 0.0
        self.fan_b_percent = 0.0

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.relay_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.fan_a_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.fan_b_gpio, GPIO.OUT, initial=GPIO.LOW)
        self.fan_a_pwm = GPIO.PWM(self.fan_a_gpio, self.pwm_freq_hz)
        self.fan_b_pwm = GPIO.PWM(self.fan_b_gpio, self.pwm_freq_hz)
        self.fan_a_pwm.start(0)
        self.fan_b_pwm.start(0)

        rospy.Subscriber("/fans/enable", Bool, self.enable_callback, queue_size=10)
        rospy.Subscriber("/fan_a/pwm_percent", Float32, self.fan_a_callback, queue_size=10)
        rospy.Subscriber("/fan_b/pwm_percent", Float32, self.fan_b_callback, queue_size=10)

    def set_a(self, percent):
        percent = max(0.0, min(100.0, percent))
        self.fan_a_pwm.ChangeDutyCycle(percent)
        self.fan_a_percent = percent

    def set_b(self, percent):
        percent = max(0.0, min(100.0, percent))
        self.fan_b_pwm.ChangeDutyCycle(percent)
        self.fan_b_percent = percent

    def enable_callback(self, msg):
        if msg.data and not self.enabled:
            GPIO.output(self.relay_gpio, GPIO.HIGH)
            rospy.sleep(self.enable_delay)
            self.set_a(self.fan_a_percent)
            self.set_b(self.fan_b_percent)
            self.enabled = True
        elif not msg.data and self.enabled:
            self.set_a(0.0)
            self.set_b(0.0)
            rospy.sleep(0.2)
            GPIO.output(self.relay_gpio, GPIO.LOW)
            self.enabled = False

    def fan_a_callback(self, msg):
        self.fan_a_percent = max(0.0, min(100.0, msg.data))
        if self.enabled:
            self.set_a(self.fan_a_percent)

    def fan_b_callback(self, msg):
        self.fan_b_percent = max(0.0, min(100.0, msg.data))
        if self.enabled:
            self.set_b(self.fan_b_percent)


def main():
    rospy.init_node("csrpi_fan_dual_bridge")
    FanDualBridge()
    rospy.spin()


if __name__ == "__main__":
    main()
