import time
from pyb import Servo


PAN_CENTER_DEG = 0
PAN_MIN_DEG = -90
PAN_MAX_DEG = 90

TILT_CENTER_DEG = 85
TILT_MIN_DEG = 0
TILT_MAX_DEG = 90

CLAW_OPEN_ANGLE = -60
CLAW_CLOSE_ANGLE = 40

CONTACT_TILT_DEG = 90
LIFT_HOLD_TILT_DEG = 70

SERVO_DELAY_MS = 200
CLAW_SETTLE_MS = 500
SEARCH_SETTLE_MS = 800
CONTACT_HOLD_MS = 500
LIFT_SETTLE_MS = 800
HOLD_SETTLE_MS = 800


def log_action(action):
    print("ACT -> " + action)


def clamp_pan(angle):
    if angle < PAN_MIN_DEG:
        return PAN_MIN_DEG
    if angle > PAN_MAX_DEG:
        return PAN_MAX_DEG
    return angle


def clamp_tilt(angle):
    if angle < TILT_MIN_DEG:
        return TILT_MIN_DEG
    if angle > TILT_MAX_DEG:
        return TILT_MAX_DEG
    return angle


def clamp_claw(angle):
    if angle < -90:
        return -90
    if angle > 90:
        return 90
    return angle


class ActuatorRig:
    def __init__(self):
        self.pan_servo = Servo(3)
        self.tilt_servo = Servo(4)
        self.claw_servo = Servo(1)
        self.pan_angle = PAN_CENTER_DEG
        self.tilt_angle = TILT_CENTER_DEG
        self.claw_angle = CLAW_CLOSE_ANGLE

    def _delay(self, delay_ms):
        if delay_ms and delay_ms > 0:
            time.sleep_ms(delay_ms)

    def pan_set(self, angle, settle_ms=0):
        self.pan_angle = clamp_pan(angle)
        log_action("PAN_SET angle={}".format(self.pan_angle))
        self.pan_servo.angle(self.pan_angle)
        self._delay(settle_ms)

    def tilt_set(self, angle, settle_ms=0):
        self.tilt_angle = clamp_tilt(angle)
        log_action("TILT_SET angle={}".format(self.tilt_angle))
        self.tilt_servo.angle(self.tilt_angle)
        self._delay(settle_ms)

    def claw_close(self, settle_ms=CLAW_SETTLE_MS):
        self.claw_angle = clamp_claw(CLAW_CLOSE_ANGLE)
        log_action("CLAW_CLOSE angle={}".format(self.claw_angle))
        self.claw_servo.angle(self.claw_angle)
        self._delay(settle_ms)

    def claw_open(self, settle_ms=CLAW_SETTLE_MS):
        self.claw_angle = clamp_claw(CLAW_OPEN_ANGLE)
        log_action("CLAW_OPEN angle={}".format(self.claw_angle))
        self.claw_servo.angle(self.claw_angle)
        self._delay(settle_ms)

    def search_pose(self, settle_ms=SEARCH_SETTLE_MS):
        log_action("SEARCH_POSE")
        self.pan_set(PAN_CENTER_DEG, 0)
        self.tilt_set(TILT_CENTER_DEG, 0)
        self.claw_close(0)
        self._delay(settle_ms)

    def center_pose(self, settle_ms=SEARCH_SETTLE_MS):
        log_action("CENTER_POSE_DEBUG")
        self.pan_set(PAN_CENTER_DEG, 0)
        self.tilt_set(TILT_CENTER_DEG, 0)
        self._delay(settle_ms)

    def contact_pose(self, settle_ms=CONTACT_HOLD_MS):
        log_action("CONTACT_POSE tilt={}".format(CONTACT_TILT_DEG))
        self.tilt_set(CONTACT_TILT_DEG, settle_ms)

    def lift_after_contact(self, settle_ms=LIFT_SETTLE_MS):
        log_action("LIFT_AFTER_CONTACT tilt={}".format(LIFT_HOLD_TILT_DEG))
        self.tilt_set(LIFT_HOLD_TILT_DEG, settle_ms)

    def hold_pose(self, settle_ms=HOLD_SETTLE_MS):
        log_action("HOLD_POSE tilt={}".format(LIFT_HOLD_TILT_DEG))
        self.tilt_set(LIFT_HOLD_TILT_DEG, settle_ms)
