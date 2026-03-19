import sensor
import image
import time
from pid import PID
from pyb import Servo, UART, Pin, Timer, millis

import cj_link

############################ C-1.2.0 configuration ############################
STATE_SCAN = 0
STATE_WAIT_PICK_WINDOW = 1
STATE_PICKING = 2

COLOR_RED = 1
COLOR_YELLOW = 2
COLOR_BLUE = 3

UART_BAUD = 9600
STABLE_FRAMES_REQUIRED = 3
HEARTBEAT_INTERVAL_MS = 1000
DEFAULT_PICK_WINDOW_MS = 10000

############################ vendor baseline motion ############################
tim = Timer(2, freq=50)
claw = tim.channel(3, Timer.PWM, pin=Pin("B10"), pulse_width_percent=7.5)
pan_servo = Servo(3)
tilt_servo = Servo(4)


def claw_angle(servo_angle):
    if servo_angle <= 0:
        servo_angle = 0
    if servo_angle >= 180:
        servo_angle = 180
    percent = (servo_angle + 45) / 18
    claw.pulse_width_percent(percent)


def obj_distance(obj_lm):
    return int(8000 / obj_lm)


def find_max(blobs):
    max_size = 0
    max_blob = None
    for blob in blobs:
        area = blob[2] * blob[3]
        if area > max_size:
            max_blob = blob
            max_size = area
    return max_blob


yellow_threshold = [(53, 99, -13, 46, 29, 57)]
red_threshold = [(38, 76, 22, 59, 0, 28)]
blue_threshold = [(33, 80, -31, 18, -56, -21)]

THRESHOLDS = {
    COLOR_RED: red_threshold,
    COLOR_YELLOW: yellow_threshold,
    COLOR_BLUE: blue_threshold,
}

pan_pid = PID(p=0.09, i=0.0, imax=90)
tilt_pid = PID(p=0.09, i=0.0, imax=90)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(20)
sensor.set_auto_whitebal(False)
clock = time.clock()

claw_angle(60)
tilt_servo.angle(30)
pan_servo.angle(90)

link = cj_link.CjLink(UART(1, UART_BAUD))
state = STATE_SCAN
last_color = 0
stable_count = 0
pending_color = 0
pick_window_ms = DEFAULT_PICK_WINDOW_MS
last_heartbeat_ms = 0
vertical_bias = -30


def reset_pose():
    pan_servo.angle(90)
    tilt_servo.angle(30)
    claw_angle(60)


def find_color_blob(img, color_id=None):
    search_order = [COLOR_RED, COLOR_YELLOW, COLOR_BLUE] if color_id is None else [color_id]
    for current_color in search_order:
        blobs = img.find_blobs(THRESHOLDS[current_color], pixels_threshold=500)
        if blobs:
            return current_color, find_max(blobs)
    return 0, None


def perform_grab_sequence(color_id):
    claw_angle(150)
    time.sleep_ms(1000)
    tilt_servo.angle(0)
    time.sleep_ms(1000)

    if color_id == COLOR_RED:
        pan_servo.angle(45)
    elif color_id == COLOR_YELLOW:
        pan_servo.angle(0)
    else:
        pan_servo.angle(-45)

    time.sleep_ms(1000)
    tilt_servo.angle(35)
    time.sleep_ms(1000)
    claw_angle(60)
    time.sleep_ms(1000)
    tilt_servo.angle(0)
    time.sleep_ms(1000)
    pan_servo.angle(90)
    time.sleep_ms(1000)


def run_pick_sequence(color_id, timeout_ms):
    align_count = 0
    start_ms = millis()

    while millis() - start_ms < timeout_ms:
        clock.tick()
        img = sensor.snapshot()
        detected_color, max_blob = find_color_blob(img, color_id)

        if detected_color == 0 or max_blob is None:
            reset_pose()
            align_count = 0
            continue

        img.draw_rectangle(max_blob.rect())
        img.draw_cross(max_blob.cx(), max_blob.cy())
        ball_s = obj_distance((max_blob[2] + max_blob[3]) / 2)

        if 60 <= ball_s <= 110:
            tilt_error = (img.height() / 2 + vertical_bias) - max_blob.cy()
            tilt_output = tilt_pid.get_pid(tilt_error, 1)
            tilt_servo.angle(tilt_servo.angle() - tilt_output)
            if abs(tilt_output) <= 0.5:
                align_count += 1
                if align_count >= 5:
                    perform_grab_sequence(color_id)
                    reset_pose()
                    return True
            else:
                align_count = 0
            continue

        align_count = 0
        if ball_s > 110:
            pan_error = img.width() / 2 - max_blob.cx()
            tilt_error = (img.height() / 2 + vertical_bias) - max_blob.cy()
            pan_output = pan_pid.get_pid(pan_error, 1) / 2
            tilt_output = tilt_pid.get_pid(tilt_error, 1)
            tilt_angle = tilt_servo.angle() - tilt_output
            if tilt_angle > 60:
                tilt_angle = 60
            if tilt_angle < -60:
                tilt_angle = -60
            tilt_servo.angle(tilt_angle)
            _ = pan_output

    reset_pose()
    return False


while True:
    clock.tick()
    now_ms = millis()

    for frame in link.poll():
        frame_type = frame["type"]
        if frame_type == cj_link.TYPE_PING:
            link.send_heartbeat(state)
        elif frame_type == cj_link.TYPE_PICK_WINDOW and state == STATE_WAIT_PICK_WINDOW:
            payload = frame["payload"]
            if len(payload) >= 2:
                pick_window_ms = payload[0] | (payload[1] << 8)
            else:
                pick_window_ms = DEFAULT_PICK_WINDOW_MS
            state = STATE_PICKING
        elif frame_type == cj_link.TYPE_ABORT and state == STATE_WAIT_PICK_WINDOW:
            state = STATE_SCAN
            pending_color = 0
            stable_count = 0
            reset_pose()

    if now_ms - last_heartbeat_ms >= HEARTBEAT_INTERVAL_MS:
        link.send_heartbeat(state)
        last_heartbeat_ms = now_ms

    if state == STATE_SCAN:
        img = sensor.snapshot()
        color_id, max_blob = find_color_blob(img)
        if color_id != 0 and max_blob is not None:
            img.draw_rectangle(max_blob.rect())
            img.draw_cross(max_blob.cx(), max_blob.cy())
            if last_color == color_id:
                stable_count += 1
            else:
                last_color = color_id
                stable_count = 1

            if stable_count >= STABLE_FRAMES_REQUIRED:
                pending_color = color_id
                link.send_color_found(color_id)
                state = STATE_WAIT_PICK_WINDOW
                stable_count = 0
        else:
            last_color = 0
            stable_count = 0
            reset_pose()
        continue

    if state == STATE_WAIT_PICK_WINDOW:
        sensor.snapshot()
        continue

    if state == STATE_PICKING:
        link.send_arm_busy(1)
        try:
            if run_pick_sequence(pending_color, pick_window_ms):
                link.send_pick_done(pending_color)
            else:
                link.send_pick_timeout(pending_color)
        except Exception:
            link.send_arm_fail(1)
        pending_color = 0
        state = STATE_SCAN
        reset_pose()