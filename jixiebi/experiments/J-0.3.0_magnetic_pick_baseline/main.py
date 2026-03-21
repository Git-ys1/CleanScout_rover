import sensor, image, time

from pid import PID
from actuator import (
    ActuatorRig,
    CONTACT_HOLD_MS,
    HOLD_SETTLE_MS,
    LIFT_SETTLE_MS,
)
from vision import (
    CLAW_OFFSET_PX,
    TARGET_MODE_BLACK_CAP,
    TARGET_MODE_GOLD_HARDWARE,
    blob_rect,
    blob_cx,
    blob_cy,
    blob_w,
    estimate_distance_proxy,
    find_target,
    get_target_config,
    target_center_error,
    target_label,
    within_approach_window,
)


STATE_SCAN = "SCAN"
STATE_TRACK = "TRACK"
STATE_APPROACH_READY = "APPROACH_READY"
STATE_CONTACT = "CONTACT"
STATE_LIFT = "LIFT"
STATE_HOLD = "HOLD"
STATE_RESET = "RESET"

TARGET_MODE = TARGET_MODE_BLACK_CAP
ENABLE_SECOND_TARGET = False

HOLD_OBSERVE_MS = 1000


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.HQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_whitebal(False)
clock = time.clock()

rig = ActuatorRig()
pan_pid = PID(p=0.05, i=0.0, imax=90)
tilt_pid = PID(p=0.05, i=0.0, imax=90)

state = STATE_RESET
ready_frames = 0


def set_state(new_state):
    global state
    if state != new_state:
        print("STATE -> " + new_state)
        state = new_state


def draw_overlay(img, blob, distance_proxy, pan_error, tilt_error):
    state_line = "STATE:{} TARGET:{}".format(state, target_label(TARGET_MODE))
    dist_line = "DIST:{:.1f} READY:{}".format(distance_proxy, ready_frames)
    err_line = "PAN:{:.1f} TILT:{:.1f}".format(pan_error, tilt_error)
    img.draw_string(0, 0, state_line, color=(255, 255, 255), mono_space=False)
    img.draw_string(0, 12, dist_line, color=(255, 255, 255), mono_space=False)
    img.draw_string(0, 24, err_line, color=(255, 255, 255), mono_space=False)
    if blob is not None:
        img.draw_rectangle(blob_rect(blob))
        img.draw_cross(blob_cx(blob), blob_cy(blob))


def reset_to_scan():
    global ready_frames
    ready_frames = 0
    pan_pid.reset_I()
    tilt_pid.reset_I()
    rig.search_pose()
    set_state(STATE_SCAN)


def track_target(pan_error, tilt_error):
    pan_output = pan_pid.get_pid(pan_error, 1) / 2
    tilt_output = tilt_pid.get_pid(tilt_error, 1)
    rig.pan_set(rig.pan_angle + pan_output, 0)
    rig.tilt_set(rig.tilt_angle - tilt_output, 0)


def perform_magnetic_pick_cycle():
    set_state(STATE_CONTACT)
    rig.contact_pose(CONTACT_HOLD_MS)

    set_state(STATE_LIFT)
    rig.lift_after_contact(LIFT_SETTLE_MS)

    set_state(STATE_HOLD)
    rig.hold_pose(HOLD_SETTLE_MS)
    time.sleep_ms(HOLD_OBSERVE_MS)

    set_state(STATE_RESET)
    rig.search_pose()


reset_to_scan()

while True:
    clock.tick()
    img = sensor.snapshot()
    blob = find_target(img, TARGET_MODE)

    if not blob:
        draw_overlay(img, None, 0, 0, 0)
        if state != STATE_SCAN:
            reset_to_scan()
        continue

    distance_proxy = estimate_distance_proxy(blob_w(blob), TARGET_MODE)
    pan_error, tilt_error = target_center_error(
        blob,
        img.width(),
        img.height(),
        CLAW_OFFSET_PX,
    )
    draw_overlay(img, blob, distance_proxy, pan_error, tilt_error)

    track_target(pan_error, tilt_error)

    if within_approach_window(distance_proxy, pan_error, tilt_error, TARGET_MODE):
        set_state(STATE_APPROACH_READY)
        ready_frames += 1
    else:
        set_state(STATE_TRACK)
        ready_frames = 0

    if ready_frames >= get_target_config(TARGET_MODE)["ready_frames"]:
        perform_magnetic_pick_cycle()
        reset_to_scan()
