from pyb import Pin, Servo, Timer

CLAW_PWM_TIMER_ID = 2
CLAW_PWM_CHANNEL = 3
CLAW_PWM_PIN = "B10"
CLAW_PWM_FREQ = 50

CLAW_OPEN_ANGLE = 60
CLAW_CLOSE_ANGLE = 150
CLAW_TEST_DELAY_MS = 1000
CLAW_CALIBRATION_ANGLES = (40, 60, 90, 120, 150, 170)

PAN_SERVO_ID = 3
TILT_SERVO_ID = 4
RESET_PAN_ANGLE = 90
RESET_TILT_ANGLE = 30
LIFT_TILT_ANGLE = 0
DROP_TILT_ANGLE = 35
RED_DROP_PAN_ANGLE = 45
YELLOW_DROP_PAN_ANGLE = 0
BLUE_DROP_PAN_ANGLE = -45
TILT_MIN_ANGLE = -60
TILT_MAX_ANGLE = 60


class ClawRig:
    def __init__(self):
        self.timer = Timer(CLAW_PWM_TIMER_ID, freq=CLAW_PWM_FREQ)
        self.claw_pwm = self.timer.channel(
            CLAW_PWM_CHANNEL,
            Timer.PWM,
            pin=Pin(CLAW_PWM_PIN),
            pulse_width_percent=7.5,
        )
        self.pan_servo = Servo(PAN_SERVO_ID)
        self.tilt_servo = Servo(TILT_SERVO_ID)

    def claw_set_angle(self, angle):
        if angle <= 0:
            angle = 0
        if angle >= 180:
            angle = 180
        percent = (angle + 45) / 18
        self.claw_pwm.pulse_width_percent(percent)

    def claw_open(self):
        self.claw_set_angle(CLAW_OPEN_ANGLE)

    def claw_close(self):
        self.claw_set_angle(CLAW_CLOSE_ANGLE)

    def reset_pose(self):
        self.pan_servo.angle(RESET_PAN_ANGLE)
        self.tilt_servo.angle(RESET_TILT_ANGLE)
        self.claw_open()

    def move_to_drop_pose(self, color_id, color_red, color_yellow):
        if color_id == color_red:
            self.pan_servo.angle(RED_DROP_PAN_ANGLE)
        elif color_id == color_yellow:
            self.pan_servo.angle(YELLOW_DROP_PAN_ANGLE)
        else:
            self.pan_servo.angle(BLUE_DROP_PAN_ANGLE)

    def clamp_tilt(self, tilt_angle):
        if tilt_angle > TILT_MAX_ANGLE:
            return TILT_MAX_ANGLE
        if tilt_angle < TILT_MIN_ANGLE:
            return TILT_MIN_ANGLE
        return tilt_angle
