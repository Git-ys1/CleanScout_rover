import sensor
import time
from pyb import millis

from claw_runtime import CLAW_CALIBRATION_ANGLES, CLAW_TEST_DELAY_MS, ClawRig

SHOW_CALIBRATION_SWEEP = False
ANGLE_SWEEP_DELAY_MS = 800

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(20)

rig = ClawRig()
rig.reset_pose()

current_label = "BOOT"
next_step_ms = millis()
step_index = 0
angle_index = 0


def show_status(label):
    img = sensor.snapshot()
    img.draw_string(2, 2, "CLAW SELFTEST", color=(255, 0, 0), scale=2)
    img.draw_string(2, 24, label, color=(0, 255, 0), scale=2)


while True:
    now_ms = millis()

    if SHOW_CALIBRATION_SWEEP:
        if now_ms >= next_step_ms:
            angle = CLAW_CALIBRATION_ANGLES[angle_index]
            current_label = "ANGLE %d" % angle
            print("CLAW_CAL -> ANGLE %d" % angle)
            rig.claw_set_angle(angle)
            angle_index = (angle_index + 1) % len(CLAW_CALIBRATION_ANGLES)
            next_step_ms = now_ms + ANGLE_SWEEP_DELAY_MS
        show_status(current_label)
        continue

    if now_ms >= next_step_ms:
        if step_index == 0:
            rig.reset_pose()
            rig.claw_open()
            current_label = "OPEN"
            print("CLAW_TEST -> OPEN")
        elif step_index == 1:
            rig.claw_close()
            current_label = "CLOSE"
            print("CLAW_TEST -> CLOSE")
        else:
            rig.claw_open()
            current_label = "OPEN"
            print("CLAW_TEST -> OPEN")

        step_index = (step_index + 1) % 3
        next_step_ms = now_ms + CLAW_TEST_DELAY_MS

    show_status(current_label)
    time.sleep_ms(50)
