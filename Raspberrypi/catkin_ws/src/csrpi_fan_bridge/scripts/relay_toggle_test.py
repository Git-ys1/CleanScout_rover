#!/usr/bin/env python3

import time

import RPi.GPIO as GPIO


def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(17, GPIO.OUT, initial=GPIO.LOW)

    for i in range(6):
        GPIO.output(17, GPIO.HIGH)
        print(f"{i}: HIGH", flush=True)
        time.sleep(1.0)
        GPIO.output(17, GPIO.LOW)
        print(f"{i}: LOW", flush=True)
        time.sleep(1.0)

    GPIO.cleanup()
    print("done", flush=True)


if __name__ == "__main__":
    main()
