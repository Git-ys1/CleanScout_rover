#!/usr/bin/env python3

import time

import RPi.GPIO as GPIO


RELAY_GPIO = 17
FAN_A_GPIO = 18
FAN_B_GPIO = 19
PWM_FREQ_HZ = 25000


def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_GPIO, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FAN_A_GPIO, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FAN_B_GPIO, GPIO.OUT, initial=GPIO.LOW)

    fan_a = GPIO.PWM(FAN_A_GPIO, PWM_FREQ_HZ)
    fan_b = GPIO.PWM(FAN_B_GPIO, PWM_FREQ_HZ)
    fan_a.start(0)
    fan_b.start(0)

    print("verify1 relay on, no pwm", flush=True)
    GPIO.output(RELAY_GPIO, GPIO.HIGH)
    time.sleep(4.0)

    print("verify2 fan A only 60%", flush=True)
    fan_a.ChangeDutyCycle(60)
    fan_b.ChangeDutyCycle(0)
    time.sleep(4.0)

    print("verify3 fan B only 60%", flush=True)
    fan_a.ChangeDutyCycle(0)
    fan_b.ChangeDutyCycle(60)
    time.sleep(4.0)

    print("verify4 fan A 30%, fan B 70%", flush=True)
    fan_a.ChangeDutyCycle(30)
    fan_b.ChangeDutyCycle(70)
    time.sleep(5.0)

    print("stop all", flush=True)
    fan_a.ChangeDutyCycle(0)
    fan_b.ChangeDutyCycle(0)
    time.sleep(0.2)
    GPIO.output(RELAY_GPIO, GPIO.LOW)

    fan_a.stop()
    fan_b.stop()
    GPIO.cleanup()


if __name__ == "__main__":
    main()
