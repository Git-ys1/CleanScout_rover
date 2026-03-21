import sensor, image, time

from pid import PID
from actuator import (
    ActuatorRig,
    CLAW_SETTLE_MS,
    COLOR_BLUE,
    COLOR_RED,
    COLOR_YELLOW,
    DROP_SETTLE_MS,
    LIFT_SETTLE_MS,
    RESET_SETTLE_MS,
)
from vision import (
    APPROACH_READY_FRAMES,
    CLAW_OFFSET_PX,
    GRAB_DISTANCE_MAX,
    GRAB_DISTANCE_MIN,
    PIXELS_THRESHOLD,
    TARGET_MODE_YELLOW,
    color_label,
    estimate_distance_proxy,
    find_target,
    target_center_error,
    within_grab_window,
)


STATE_SCAN = 'SCAN'
STATE_TRACK = 'TRACK'
STATE_APPROACH_READY = 'APPROACH_READY'
STATE_GRAB = 'GRAB'
STATE_DROP = 'DROP'
STATE_RESET = 'RESET'

TARGET_MODE = TARGET_MODE_YELLOW
ENABLE_COLOR_SORTING = False


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
active_color_id = COLOR_YELLOW


def set_state(new_state):
    global state
    if state != new_state:
        print('STATE -> ' + new_state)
        state = new_state


def draw_overlay(img, color_id, distance_proxy, pan_error, tilt_error):
    state_line = 'STATE:{} COLOR:{}'.format(state, color_label(color_id))
    dist_line = 'DIST:{:.1f} READY:{}'.format(distance_proxy, ready_frames)
    err_line = 'PAN:{:.1f} TILT:{:.1f}'.format(pan_error, tilt_error)
    img.draw_string(0, 0, state_line, color=(255, 255, 255), mono_space=False)
    img.draw_string(0, 12, dist_line, color=(255, 255, 255), mono_space=False)
    img.draw_string(0, 24, err_line, color=(255, 255, 255), mono_space=False)


def reset_to_scan():
    global ready_frames, active_color_id
    ready_frames = 0
    active_color_id = COLOR_YELLOW
    pan_pid.reset_I()
    tilt_pid.reset_I()
    rig.center_pose(RESET_SETTLE_MS)
    set_state(STATE_SCAN)


def track_target(pan_error, tilt_error):
    pan_output = pan_pid.get_pid(pan_error, 1) / 2
    tilt_output = tilt_pid.get_pid(tilt_error, 1)
    rig.pan_set(rig.pan_angle + pan_output, 0)
    rig.tilt_set(rig.tilt_angle - tilt_output, 0)


def perform_grab_cycle(color_id):
    set_state(STATE_GRAB)
    rig.claw_close(CLAW_SETTLE_MS)

    rig.lift_pose(LIFT_SETTLE_MS)

    set_state(STATE_DROP)
    rig.drop_pose_for(color_id, DROP_SETTLE_MS)
    rig.claw_open(CLAW_SETTLE_MS)

    set_state(STATE_RESET)
    rig.center_pose(RESET_SETTLE_MS)


reset_to_scan()

while True:
    clock.tick()
    img = sensor.snapshot()
    color_id, blob = find_target(
        img,
        target_mode=TARGET_MODE,
        enable_color_sorting=ENABLE_COLOR_SORTING,
        pixels_threshold=PIXELS_THRESHOLD,
    )

    if not blob:
        draw_overlay(img, 0, 0, 0, 0)
        if state != STATE_SCAN:
            reset_to_scan()
        continue

    active_color_id = color_id
    img.draw_rectangle(blob.rect())
    img.draw_cross(blob.cx(), blob.cy())

    distance_proxy = estimate_distance_proxy(blob[2])
    pan_error, tilt_error = target_center_error(
        blob,
        img.width(),
        img.height(),
        CLAW_OFFSET_PX,
    )
    draw_overlay(img, color_id, distance_proxy, pan_error, tilt_error)

    track_target(pan_error, tilt_error)

    if within_grab_window(distance_proxy, pan_error, tilt_error):
        set_state(STATE_APPROACH_READY)
        ready_frames += 1
    else:
        set_state(STATE_TRACK)
        ready_frames = 0

    if ready_frames >= APPROACH_READY_FRAMES:
        perform_grab_cycle(active_color_id)
        reset_to_scan()
