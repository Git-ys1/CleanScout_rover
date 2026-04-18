#!/usr/bin/env python3

import time

import RPi.GPIO as GPIO


RELAY_GPIO = 17
PWM_GPIO = 18
FG_FRONT_GPIO = 23
FG_REAR_GPIO = 24
PWM_FREQ_HZ = 25000


def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_GPIO, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PWM_GPIO, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FG_FRONT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(FG_REAR_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    pwm = GPIO.PWM(PWM_GPIO, PWM_FREQ_HZ)
    pwm.start(0)

    print("relay on", flush=True)
    GPIO.output(RELAY_GPIO, GPIO.HIGH)
    time.sleep(0.2)

    for percent in (0, 30, 60, 100):
        print(f"set fan pwm percent={percent}", flush=True)
        pwm.ChangeDutyCycle(percent)
        time.sleep(4.0)

    print("stop fan", flush=True)
    pwm.ChangeDutyCycle(0)
    time.sleep(0.2)
    GPIO.output(RELAY_GPIO, GPIO.LOW)
    pwm.stop()
    GPIO.cleanup()


if __name__ == "__main__":
    main()
