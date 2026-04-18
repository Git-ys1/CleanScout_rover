import time
from pyb import Pin, Timer


TEST_DELAY_MS = 1000

tim = Timer(2, freq=50)
claw = tim.channel(3, Timer.PWM, pin=Pin("B10"), pulse_width_percent=7.5)


def claw_angle(servo_angle):
    if servo_angle <= 0:
        servo_angle = 0
    if servo_angle >= 180:
        servo_angle = 180
    percent = (servo_angle + 45) / 18
    claw.pulse_width_percent(percent)


def run_step(angle):
    print("VENDOR_CLAW -> {}".format(angle))
    claw_angle(angle)
    time.sleep_ms(TEST_DELAY_MS)


while True:
    run_step(60)
    run_step(150)
    run_step(60)
