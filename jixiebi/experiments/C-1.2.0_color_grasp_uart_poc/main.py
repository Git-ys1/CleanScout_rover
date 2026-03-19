import sensor
import image
import time
from pid import PID
from pyb import Servo, UART, Pin, Timer, millis

import cj_link

############################ C-1.2.1 configuration ############################
STATE_SCAN = 0
STATE_WAIT_PICK_WINDOW = 1
STATE_LOCAL_PICK_FALLBACK = 2
STATE_PICKING = 3
STATE_DONE = 4
STATE_TIMEOUT = 5
STATE_FAIL = 6

COLOR_RED = 1
COLOR_YELLOW = 2
COLOR_BLUE = 3

UART_BAUD = 9600
STABLE_FRAMES_REQUIRED = 3
HEARTBEAT_INTERVAL_MS = 1000
DEFAULT_PICK_WINDOW_MS = 10000
WAIT_PICK_WINDOW_TIMEOUT_MS = 2000
LOCAL_PICK_FALLBACK_DELAY_MS = 1400
COLOR_FOUND_RETRY_INTERVAL_MS = 400
MAX_COLOR_FOUND_RETRIES = 4
POST_PICK_COOLDOWN_MS = 1800
PIXELS_THRESHOLD = 500
VERTICAL_BIAS = -30

RED_THRESHOLD = [(38, 76, 22, 59, 0, 28)]
YELLOW_THRESHOLD = [(53, 99, -13, 46, 29, 57)]
BLUE_THRESHOLD = [(33, 80, -31, 18, -56, -21)]

THRESHOLDS = {
    COLOR_RED: RED_THRESHOLD,
    COLOR_YELLOW: YELLOW_THRESHOLD,
    COLOR_BLUE: BLUE_THRESHOLD,
}

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
state_entered_ms = millis()
last_color = 0
stable_count = 0
pending_color = 0
pick_window_ms = DEFAULT_PICK_WINDOW_MS
last_heartbeat_ms = 0
wait_started_ms = 0
last_color_found_tx_ms = 0
color_found_retry_count = 0
result_hold_until_ms = 0
state_banner_text = ""
state_banner_until_ms = 0


def color_name(color_id):
    if color_id == COLOR_RED:
        return "RED"
    if color_id == COLOR_YELLOW:
        return "YELLOW"
    if color_id == COLOR_BLUE:
        return "BLUE"
    return "NONE"


def state_label(current_state):
    if current_state == STATE_SCAN:
        return "SCAN"
    if current_state == STATE_WAIT_PICK_WINDOW:
        return "WAIT_PICK_WINDOW"
    if current_state == STATE_LOCAL_PICK_FALLBACK:
        return "LOCAL_PICK_FALLBACK"
    if current_state == STATE_PICKING:
        return "PICKING"
    if current_state == STATE_DONE:
        return "DONE"
    if current_state == STATE_TIMEOUT:
        return "TIMEOUT"
    if current_state == STATE_FAIL:
        return "FAIL"
    return "UNKNOWN"


def set_state(new_state, banner_text=None, banner_hold_ms=0):
    global state
    global state_entered_ms
    global state_banner_text
    global state_banner_until_ms

    state = new_state
    state_entered_ms = millis()
    print("[CJ] STATE -> " + state_label(new_state))

    if banner_text is not None:
        state_banner_text = banner_text
        state_banner_until_ms = state_entered_ms + banner_hold_ms
        print("[CJ] EVENT -> " + banner_text)


def current_status_text(now_ms):
    if state_banner_text and now_ms <= state_banner_until_ms:
        return state_banner_text
    return state_label(state)


def draw_status(img, now_ms):
    status_text = current_status_text(now_ms)
    color_text = color_name(pending_color)
    img.draw_string(2, 2, status_text, color=(255, 0, 0), scale=2)
    img.draw_string(2, 22, "TARGET:" + color_text, color=(0, 255, 0), scale=1)


def begin_wait_pick_window(color_id, now_ms):
    global pending_color
    global wait_started_ms
    global last_color_found_tx_ms
    global color_found_retry_count
    global stable_count

    pending_color = color_id
    wait_started_ms = now_ms
    last_color_found_tx_ms = now_ms
    color_found_retry_count = 0
    stable_count = 0
    link.send_color_found(color_id)
    set_state(STATE_WAIT_PICK_WINDOW, "COLOR_FOUND", 500)


def reset_pose():
    pan_servo.angle(90)
    tilt_servo.angle(30)
    claw_angle(60)


def reset_to_scan():
    global last_color
    global stable_count
    global pending_color
    global color_found_retry_count
    global wait_started_ms
    global last_color_found_tx_ms

    last_color = 0
    stable_count = 0
    pending_color = 0
    color_found_retry_count = 0
    wait_started_ms = 0
    last_color_found_tx_ms = 0
    reset_pose()
    set_state(STATE_SCAN)


def find_color_blob(img, color_id=None):
    search_order = [COLOR_RED, COLOR_YELLOW, COLOR_BLUE] if color_id is None else [color_id]
    for current_color in search_order:
        blobs = img.find_blobs(THRESHOLDS[current_color], pixels_threshold=PIXELS_THRESHOLD)
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
        draw_status(img, millis())

        if detected_color == 0 or max_blob is None:
            reset_pose()
            align_count = 0
            continue

        img.draw_rectangle(max_blob.rect())
        img.draw_cross(max_blob.cx(), max_blob.cy())
        ball_s = obj_distance((max_blob[2] + max_blob[3]) / 2)

        if 60 <= ball_s <= 110:
            tilt_error = (img.height() / 2 + VERTICAL_BIAS) - max_blob.cy()
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
            tilt_error = (img.height() / 2 + VERTICAL_BIAS) - max_blob.cy()
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


reset_to_scan()

while True:
    clock.tick()
    now_ms = millis()
    img = sensor.snapshot()
    draw_status(img, now_ms)

    for frame in link.poll():
        frame_type = frame["type"]
        if frame_type == cj_link.TYPE_PING:
            print("[CJ] RX PING")
            link.send_heartbeat(state)
        elif frame_type == cj_link.TYPE_PICK_WINDOW and (state == STATE_WAIT_PICK_WINDOW or state == STATE_LOCAL_PICK_FALLBACK):
            payload = frame["payload"]
            if len(payload) >= 2:
                pick_window_ms = payload[0] | (payload[1] << 8)
            else:
                pick_window_ms = DEFAULT_PICK_WINDOW_MS
            print("[CJ] RX PICK_WINDOW timeout_ms=" + str(pick_window_ms))
            link.send_arm_busy(1)
            set_state(STATE_PICKING)
        elif frame_type == cj_link.TYPE_ABORT and (state == STATE_WAIT_PICK_WINDOW or state == STATE_LOCAL_PICK_FALLBACK):
            print("[CJ] RX ABORT")
            reset_to_scan()

    if now_ms - last_heartbeat_ms >= HEARTBEAT_INTERVAL_MS:
        link.send_heartbeat(state)
        last_heartbeat_ms = now_ms

    if state == STATE_SCAN:
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
                begin_wait_pick_window(color_id, now_ms)
        else:
            last_color = 0
            stable_count = 0
            reset_pose()
        continue

    if state == STATE_WAIT_PICK_WINDOW:
        detected_color, max_blob = find_color_blob(img, pending_color)
        target_visible = detected_color == pending_color and max_blob is not None

        if target_visible:
            img.draw_rectangle(max_blob.rect())
            img.draw_cross(max_blob.cx(), max_blob.cy())

        if (now_ms - last_color_found_tx_ms) >= COLOR_FOUND_RETRY_INTERVAL_MS and color_found_retry_count < MAX_COLOR_FOUND_RETRIES:
            color_found_retry_count += 1
            last_color_found_tx_ms = now_ms
            link.send_color_found(pending_color)
            print("[CJ] RETRY COLOR_FOUND count=" + str(color_found_retry_count))

        if target_visible and (now_ms - wait_started_ms) >= LOCAL_PICK_FALLBACK_DELAY_MS:
            print("[CJ] LOCAL PICK FALLBACK")
            set_state(STATE_LOCAL_PICK_FALLBACK)
            continue

        if (now_ms - wait_started_ms) >= WAIT_PICK_WINDOW_TIMEOUT_MS:
            print("[CJ] WAIT_PICK_WINDOW timeout -> SCAN")
            reset_to_scan()
        continue

    if state == STATE_LOCAL_PICK_FALLBACK:
        if (now_ms - state_entered_ms) < 200:
            continue
        link.send_arm_busy(1)
        set_state(STATE_PICKING, "LOCAL_PICK_FALLBACK", 500)
        continue

    if state == STATE_PICKING:
        try:
            if run_pick_sequence(pending_color, pick_window_ms):
                link.send_pick_done(pending_color)
                result_hold_until_ms = millis() + POST_PICK_COOLDOWN_MS
                set_state(STATE_DONE)
            else:
                link.send_pick_timeout(pending_color)
                result_hold_until_ms = millis() + POST_PICK_COOLDOWN_MS
                set_state(STATE_TIMEOUT)
        except Exception as exc:
            print("[CJ] PICK FAIL: " + str(exc))
            link.send_arm_fail(1)
            result_hold_until_ms = millis() + POST_PICK_COOLDOWN_MS
            set_state(STATE_FAIL)
        pending_color = 0
        reset_pose()
        continue

    if state == STATE_DONE or state == STATE_TIMEOUT or state == STATE_FAIL:
        if now_ms >= result_hold_until_ms:
            reset_to_scan()
