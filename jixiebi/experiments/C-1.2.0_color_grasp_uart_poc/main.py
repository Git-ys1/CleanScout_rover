import sensor
import image
import time
from pid import PID
from pyb import UART, millis

import cj_link
from claw_runtime import (
    CLAW_CLOSE_ANGLE,
    CLAW_OPEN_ANGLE,
    CLAW_TEST_DELAY_MS,
    ClawRig,
    DROP_TILT_ANGLE,
    LIFT_TILT_ANGLE,
)

############################ C-1.2.3 configuration ############################
STATE_SCAN = 0
STATE_WAIT_PICK_WINDOW = 1
STATE_LOCAL_PICK_FALLBACK = 2
STATE_PICKING = 3
STATE_DONE = 4
STATE_TIMEOUT = 5
STATE_FAIL = 6
STATE_SELFTEST = 7

MODE_CLAW_SELFTEST = 0
MODE_FORCE_LOCAL_GRAB = 1
MODE_VISION_LOCAL_GRAB = 2
MODE_CJ_LINKED = 3

RUN_MODE = MODE_FORCE_LOCAL_GRAB

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
GRAB_STEP_DELAY_MS = 1000
FORCE_LOCAL_GRAB_DELAY_MS = 1200
FORCE_LOCAL_GRAB_COLOR = COLOR_YELLOW

RED_THRESHOLD = [(38, 76, 22, 59, 0, 28)]
YELLOW_THRESHOLD = [(53, 99, -13, 46, 29, 57)]
BLUE_THRESHOLD = [(33, 80, -31, 18, -56, -21)]

THRESHOLDS = {
    COLOR_RED: RED_THRESHOLD,
    COLOR_YELLOW: YELLOW_THRESHOLD,
    COLOR_BLUE: BLUE_THRESHOLD,
}

pan_pid = PID(p=0.09, i=0.0, imax=90)
tilt_pid = PID(p=0.09, i=0.0, imax=90)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(20)
sensor.set_auto_whitebal(False)
clock = time.clock()

rig = ClawRig()
rig.reset_pose()

link = cj_link.CjLink(UART(1, UART_BAUD))
boot_ms = millis()
state = STATE_SCAN
state_entered_ms = boot_ms
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
force_local_grab_done = False
selftest_step_index = 0
selftest_next_ms = boot_ms


def color_name(color_id):
    if color_id == COLOR_RED:
        return "RED"
    if color_id == COLOR_YELLOW:
        return "YELLOW"
    if color_id == COLOR_BLUE:
        return "BLUE"
    return "NONE"


def mode_label(mode):
    if mode == MODE_CLAW_SELFTEST:
        return "MODE_CLAW_SELFTEST"
    if mode == MODE_FORCE_LOCAL_GRAB:
        return "MODE_FORCE_LOCAL_GRAB"
    if mode == MODE_VISION_LOCAL_GRAB:
        return "MODE_VISION_LOCAL_GRAB"
    if mode == MODE_CJ_LINKED:
        return "MODE_CJ_LINKED"
    return "MODE_UNKNOWN"


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
    if current_state == STATE_SELFTEST:
        return "SELFTEST"
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
    img.draw_string(2, 2, mode_label(RUN_MODE), color=(255, 255, 0), scale=1)
    img.draw_string(2, 18, current_status_text(now_ms), color=(255, 0, 0), scale=2)
    img.draw_string(2, 40, "TARGET:" + color_name(pending_color), color=(0, 255, 0), scale=1)
    img.draw_string(2, 54, "CLAW O/C:%d/%d" % (CLAW_OPEN_ANGLE, CLAW_CLOSE_ANGLE), color=(0, 200, 255), scale=1)


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
    rig.reset_pose()


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


def claw_open():
    print("[CJ] CLAW -> OPEN angle=%d" % CLAW_OPEN_ANGLE)
    rig.claw_open()


def claw_close():
    print("[CJ] CLAW -> CLOSE angle=%d" % CLAW_CLOSE_ANGLE)
    rig.claw_close()


def claw_set_angle(angle):
    print("[CJ] CLAW -> SET angle=%d" % angle)
    rig.claw_set_angle(angle)


def perform_grab_sequence(color_id):
    print("[CJ] GRAB -> CLOSE_CLAW")
    claw_close()
    time.sleep_ms(GRAB_STEP_DELAY_MS)

    print("[CJ] GRAB -> LIFT")
    rig.tilt_servo.angle(LIFT_TILT_ANGLE)
    time.sleep_ms(GRAB_STEP_DELAY_MS)

    print("[CJ] GRAB -> MOVE_TO_DROP")
    rig.move_to_drop_pose(color_id, COLOR_RED, COLOR_YELLOW)
    time.sleep_ms(GRAB_STEP_DELAY_MS)

    print("[CJ] GRAB -> LOWER_FOR_DROP")
    rig.tilt_servo.angle(DROP_TILT_ANGLE)
    time.sleep_ms(GRAB_STEP_DELAY_MS)

    print("[CJ] GRAB -> OPEN_CLAW")
    claw_open()
    time.sleep_ms(GRAB_STEP_DELAY_MS)

    print("[CJ] GRAB -> RESET_POSE")
    reset_pose()
    time.sleep_ms(GRAB_STEP_DELAY_MS)


def finalize_pick_result(success, color_id, origin_label):
    global pending_color
    global result_hold_until_ms
    global force_local_grab_done

    if success:
        link.send_pick_done(color_id)
        set_state(STATE_DONE, origin_label + " DONE", 800)
    else:
        link.send_pick_timeout(color_id)
        set_state(STATE_TIMEOUT, origin_label + " TIMEOUT", 800)

    result_hold_until_ms = millis() + POST_PICK_COOLDOWN_MS
    pending_color = 0

    if RUN_MODE == MODE_FORCE_LOCAL_GRAB:
        force_local_grab_done = True


def fail_pick_result(origin_label, reason_code=1):
    global pending_color
    global result_hold_until_ms
    global force_local_grab_done

    link.send_arm_fail(reason_code)
    set_state(STATE_FAIL, origin_label + " FAIL", 800)
    result_hold_until_ms = millis() + POST_PICK_COOLDOWN_MS
    pending_color = 0

    if RUN_MODE == MODE_FORCE_LOCAL_GRAB:
        force_local_grab_done = True


def execute_direct_grab(color_id, origin_label):
    try:
        perform_grab_sequence(color_id)
        finalize_pick_result(True, color_id, origin_label)
    except Exception as exc:
        print("[CJ] PICK FAIL: " + str(exc))
        fail_pick_result(origin_label, 1)


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
            rig.tilt_servo.angle(rig.tilt_servo.angle() - tilt_output)
            if abs(tilt_output) <= 0.5:
                align_count += 1
                if align_count >= 5:
                    perform_grab_sequence(color_id)
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
            tilt_angle = rig.clamp_tilt(rig.tilt_servo.angle() - tilt_output)
            rig.tilt_servo.angle(tilt_angle)
            _ = pan_output

    reset_pose()
    return False


def execute_vision_pick(color_id, timeout_ms, origin_label):
    try:
        success = run_pick_sequence(color_id, timeout_ms)
        finalize_pick_result(success, color_id, origin_label)
    except Exception as exc:
        print("[CJ] PICK FAIL: " + str(exc))
        fail_pick_result(origin_label, 1)


def run_claw_selftest_cycle(now_ms):
    global selftest_step_index
    global selftest_next_ms

    if now_ms < selftest_next_ms:
        return

    if selftest_step_index == 0:
        claw_open()
        set_state(STATE_SELFTEST, "CLAW_TEST OPEN", CLAW_TEST_DELAY_MS)
    elif selftest_step_index == 1:
        claw_close()
        set_state(STATE_SELFTEST, "CLAW_TEST CLOSE", CLAW_TEST_DELAY_MS)
    else:
        claw_open()
        set_state(STATE_SELFTEST, "CLAW_TEST OPEN", CLAW_TEST_DELAY_MS)

    selftest_step_index = (selftest_step_index + 1) % 3
    selftest_next_ms = now_ms + CLAW_TEST_DELAY_MS


reset_pose()
if RUN_MODE == MODE_CLAW_SELFTEST:
    set_state(STATE_SELFTEST, "CLAW_TEST OPEN", CLAW_TEST_DELAY_MS)

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
        elif RUN_MODE == MODE_CJ_LINKED and frame_type == cj_link.TYPE_PICK_WINDOW and (state == STATE_WAIT_PICK_WINDOW or state == STATE_LOCAL_PICK_FALLBACK):
            payload = frame["payload"]
            if len(payload) >= 2:
                pick_window_ms = payload[0] | (payload[1] << 8)
            else:
                pick_window_ms = DEFAULT_PICK_WINDOW_MS
            print("[CJ] RX PICK_WINDOW timeout_ms=" + str(pick_window_ms))
            link.send_arm_busy(1)
            set_state(STATE_PICKING, "PICK_WINDOW", 500)
        elif RUN_MODE == MODE_CJ_LINKED and frame_type == cj_link.TYPE_ABORT and (state == STATE_WAIT_PICK_WINDOW or state == STATE_LOCAL_PICK_FALLBACK):
            print("[CJ] RX ABORT")
            reset_to_scan()

    if now_ms - last_heartbeat_ms >= HEARTBEAT_INTERVAL_MS:
        link.send_heartbeat(state)
        last_heartbeat_ms = now_ms

    if state == STATE_DONE or state == STATE_TIMEOUT or state == STATE_FAIL:
        if RUN_MODE == MODE_FORCE_LOCAL_GRAB:
            continue
        if now_ms >= result_hold_until_ms:
            reset_to_scan()
        continue

    if RUN_MODE == MODE_CLAW_SELFTEST:
        run_claw_selftest_cycle(now_ms)
        continue

    if RUN_MODE == MODE_FORCE_LOCAL_GRAB:
        if not force_local_grab_done and (now_ms - boot_ms) >= FORCE_LOCAL_GRAB_DELAY_MS:
            pending_color = FORCE_LOCAL_GRAB_COLOR
            set_state(STATE_PICKING, "FORCE_LOCAL_GRAB", 500)
            execute_direct_grab(pending_color, "FORCE_LOCAL_GRAB")
        continue

    if RUN_MODE == MODE_VISION_LOCAL_GRAB:
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
                stable_count = 0
                set_state(STATE_PICKING, "VISION_LOCAL_GRAB", 500)
                execute_vision_pick(color_id, DEFAULT_PICK_WINDOW_MS, "VISION_LOCAL_GRAB")
        else:
            last_color = 0
            stable_count = 0
            reset_pose()
        continue

    if RUN_MODE != MODE_CJ_LINKED:
        continue

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
            set_state(STATE_LOCAL_PICK_FALLBACK, "LOCAL_PICK_FALLBACK", 500)
            continue

        if (now_ms - wait_started_ms) >= WAIT_PICK_WINDOW_TIMEOUT_MS:
            print("[CJ] WAIT_PICK_WINDOW timeout -> SCAN")
            reset_to_scan()
        continue

    if state == STATE_LOCAL_PICK_FALLBACK:
        link.send_arm_busy(1)
        set_state(STATE_PICKING, "LOCAL_PICK_FALLBACK", 500)
        execute_vision_pick(pending_color, pick_window_ms, "LOCAL_PICK_FALLBACK")
        continue

    if state == STATE_PICKING:
        if pending_color != 0:
            execute_vision_pick(pending_color, pick_window_ms, "CJ_LINKED")
        continue
