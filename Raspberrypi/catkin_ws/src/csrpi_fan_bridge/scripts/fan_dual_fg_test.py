#!/usr/bin/env python3

import time

import RPi.GPIO as GPIO


RELAY_GPIO = 17
FAN_A_GPIO = 18
FAN_B_GPIO = 19
FAN_A_FG_IN = 23
FAN_A_FG_OUT = 24
FAN_B_FG_IN = 25
FAN_B_FG_OUT = 16
PWM_FREQ_HZ = 25000


def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_GPIO, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FAN_A_GPIO, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FAN_B_GPIO, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FAN_A_FG_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(FAN_A_FG_OUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(FAN_B_FG_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(FAN_B_FG_OUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    counts = {
        "a_in": 0,
        "a_out": 0,
        "b_in": 0,
        "b_out": 0,
    }

    edge_counts = {
        "a_in": {"rising": 0, "falling": 0},
        "a_out": {"rising": 0, "falling": 0},
        "b_in": {"rising": 0, "falling": 0},
        "b_out": {"rising": 0, "falling": 0},
    }

    last_levels = {
        "a_in": GPIO.input(FAN_A_FG_IN),
        "a_out": GPIO.input(FAN_A_FG_OUT),
        "b_in": GPIO.input(FAN_B_FG_IN),
        "b_out": GPIO.input(FAN_B_FG_OUT),
    }

    def make_callback(name, pin):
        def callback(channel):
            level = GPIO.input(pin)
            if level != last_levels[name]:
                if level:
                    edge_counts[name]["rising"] += 1
                else:
                    edge_counts[name]["falling"] += 1
                counts[name] += 1
                last_levels[name] = level
        return callback

    GPIO.add_event_detect(FAN_A_FG_IN, GPIO.BOTH, callback=make_callback("a_in", FAN_A_FG_IN), bouncetime=1)
    GPIO.add_event_detect(FAN_A_FG_OUT, GPIO.BOTH, callback=make_callback("a_out", FAN_A_FG_OUT), bouncetime=1)
    GPIO.add_event_detect(FAN_B_FG_IN, GPIO.BOTH, callback=make_callback("b_in", FAN_B_FG_IN), bouncetime=1)
    GPIO.add_event_detect(FAN_B_FG_OUT, GPIO.BOTH, callback=make_callback("b_out", FAN_B_FG_OUT), bouncetime=1)

    fan_a = GPIO.PWM(FAN_A_GPIO, PWM_FREQ_HZ)
    fan_b = GPIO.PWM(FAN_B_GPIO, PWM_FREQ_HZ)
    fan_a.start(0)
    fan_b.start(0)

    print("fg test relay on", flush=True)
    GPIO.output(RELAY_GPIO, GPIO.HIGH)
    time.sleep(0.2)

    print("fg phase 1: fan A only 60%", flush=True)
    counts.update(a_in=0, a_out=0, b_in=0, b_out=0)
    edge_counts.update(a_in={"rising": 0, "falling": 0}, a_out={"rising": 0, "falling": 0}, b_in={"rising": 0, "falling": 0}, b_out={"rising": 0, "falling": 0})
    fan_a.ChangeDutyCycle(60)
    fan_b.ChangeDutyCycle(0)
    time.sleep(5.0)
    print(f"counts phase1: {counts}", flush=True)
    print(f"edges phase1: {edge_counts}", flush=True)

    print("fg phase 2: fan B only 60%", flush=True)
    counts.update(a_in=0, a_out=0, b_in=0, b_out=0)
    edge_counts.update(a_in={"rising": 0, "falling": 0}, a_out={"rising": 0, "falling": 0}, b_in={"rising": 0, "falling": 0}, b_out={"rising": 0, "falling": 0})
    fan_a.ChangeDutyCycle(0)
    fan_b.ChangeDutyCycle(60)
    time.sleep(5.0)
    print(f"counts phase2: {counts}", flush=True)
    print(f"edges phase2: {edge_counts}", flush=True)

    print("fg stop all", flush=True)
    fan_a.ChangeDutyCycle(0)
    fan_b.ChangeDutyCycle(0)
    time.sleep(0.2)
    GPIO.output(RELAY_GPIO, GPIO.LOW)

    fan_a.stop()
    fan_b.stop()
    GPIO.cleanup()


if __name__ == "__main__":
    main()
