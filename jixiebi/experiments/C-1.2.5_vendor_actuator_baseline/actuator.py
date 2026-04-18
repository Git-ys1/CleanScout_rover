import time
from pyb import Servo


PAN_CENTER_DEG = 0
TILT_CENTER_DEG = 85
PAN_STEP_DEG = 2
TILT_STEP_DEG = 2
SERVO_DELAY_MS = 200
LOOP_PAUSE_MS = 1000
PAN_CALIBRATION_DELAY_MS = 900
TILT_CALIBRATION_DELAY_MS = 900

PAN_MIN_DEG = -90
PAN_MAX_DEG = 90
TILT_MIN_DEG = 0
TILT_MAX_DEG = 90
CLAW_MIN_DEG = -90
CLAW_MAX_DEG = 90

# Vendor seed was Servo(1).angle(50). Freeze actual claw limits from hardware.
CLAW_CLOSE_SEED = 50
CLAW_OPEN_ANGLE = -60
CLAW_CLOSE_ANGLE = 40
CLAW_CALIBRATION_ANGLES = (-60, -30, 0, 20, 30, 40)
CLAW_CALIBRATION_DELAY_MS = 900
PAN_CALIBRATION_ANGLES = (-90, -60, -30, 0, 30, 60, 90)
TILT_CALIBRATION_ANGLES = (0, 10, 20, 30, 60, 85, 90)


def log_action(action):
    print("ACT -> " + action)


def clamp_angle(value, minimum, maximum):
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


class ActuatorRig:
    def __init__(self):
        self.pan_servo = Servo(3)
        self.tilt_servo = Servo(4)
        self.claw_servo = Servo(1)
        self.pan_angle = PAN_CENTER_DEG
        self.tilt_angle = TILT_CENTER_DEG
        self.claw_angle = CLAW_OPEN_ANGLE

    def _delay(self, delay_ms):
        time.sleep_ms(delay_ms)

    def _set_pan(self, target, action):
        self.pan_angle = clamp_angle(target, PAN_MIN_DEG, PAN_MAX_DEG)
        log_action(action + " angle={}".format(self.pan_angle))
        self.pan_servo.angle(self.pan_angle)
        self._delay(SERVO_DELAY_MS)

    def _set_tilt(self, target, action):
        self.tilt_angle = clamp_angle(target, TILT_MIN_DEG, TILT_MAX_DEG)
        log_action(action + " angle={}".format(self.tilt_angle))
        self.tilt_servo.angle(self.tilt_angle)
        self._delay(SERVO_DELAY_MS)

    def _set_claw(self, target, action):
        self.claw_angle = clamp_angle(target, CLAW_MIN_DEG, CLAW_MAX_DEG)
        log_action(action + " angle={}".format(self.claw_angle))
        self.claw_servo.angle(self.claw_angle)
        self._delay(SERVO_DELAY_MS)

    def pan_left_step(self):
        self._set_pan(self.pan_angle + PAN_STEP_DEG, "PAN_LEFT")

    def pan_right_step(self):
        self._set_pan(self.pan_angle - PAN_STEP_DEG, "PAN_RIGHT")

    def tilt_up_step(self):
        self._set_tilt(self.tilt_angle - TILT_STEP_DEG, "TILT_UP")

    def tilt_down_step(self):
        self._set_tilt(self.tilt_angle + TILT_STEP_DEG, "TILT_DOWN")

    def pan_center(self):
        self._set_pan(PAN_CENTER_DEG, "PAN_CENTER")

    def tilt_center(self):
        self._set_tilt(TILT_CENTER_DEG, "TILT_CENTER")

    def pan_to_angle(self, angle):
        self._set_pan(angle, "PAN_CAL")

    def tilt_to_angle(self, angle):
        self._set_tilt(angle, "TILT_CAL")

    def center_all(self):
        log_action("CENTER")
        self.pan_servo.angle(PAN_CENTER_DEG)
        self.tilt_servo.angle(TILT_CENTER_DEG)
        self.pan_angle = PAN_CENTER_DEG
        self.tilt_angle = TILT_CENTER_DEG
        self._delay(SERVO_DELAY_MS)

    def claw_open(self):
        self._set_claw(CLAW_OPEN_ANGLE, "CLAW_OPEN")

    def claw_close(self):
        self._set_claw(CLAW_CLOSE_ANGLE, "CLAW_CLOSE")

    def claw_to_angle(self, angle):
        self._set_claw(angle, "CLAW_CAL")
