#!/usr/bin/env python3

import time

import pigpio
import rospy


RELAY_GPIO = 17
PWM_GPIO = 18
FG_FRONT_GPIO = 23
FG_REAR_GPIO = 24
PWM_FREQ_HZ = 25000


def set_pwm_percent(pi, percent):
    duty = int(max(0.0, min(100.0, percent)) * 10000)
    pi.hardware_PWM(PWM_GPIO, PWM_FREQ_HZ, duty)


def main():
    rospy.init_node("fan_pwm_test")
    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("pigpio daemon is not running")

    pi.set_mode(RELAY_GPIO, pigpio.OUTPUT)
    pi.set_mode(FG_FRONT_GPIO, pigpio.INPUT)
    pi.set_mode(FG_REAR_GPIO, pigpio.INPUT)
    pi.set_pull_up_down(FG_FRONT_GPIO, pigpio.PUD_UP)
    pi.set_pull_up_down(FG_REAR_GPIO, pigpio.PUD_UP)

    rospy.loginfo("relay on")
    pi.write(RELAY_GPIO, 1)
    time.sleep(0.2)

    for percent in (0, 30, 60, 100):
        rospy.loginfo("set fan pwm percent=%s", percent)
        set_pwm_percent(pi, percent)
        time.sleep(4.0)

    rospy.loginfo("stop fan")
    set_pwm_percent(pi, 0)
    time.sleep(0.2)
    pi.write(RELAY_GPIO, 0)
    pi.stop()


if __name__ == "__main__":
    main()
