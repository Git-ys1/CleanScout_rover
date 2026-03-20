import time
from pyb import millis

from actuator import (
    ActuatorRig,
    CLAW_CALIBRATION_ANGLES,
    CLAW_CALIBRATION_DELAY_MS,
    LOOP_PAUSE_MS,
    PAN_CALIBRATION_ANGLES,
    PAN_CALIBRATION_DELAY_MS,
    TILT_CALIBRATION_ANGLES,
    TILT_CALIBRATION_DELAY_MS,
)
from command_source import (
    CMD_CENTER,
    CMD_CLAW_CLOSE,
    CMD_CLAW_OPEN,
    CMD_DEMO_LOOP_START,
    CMD_PAN_LEFT,
    CMD_PAN_RIGHT,
    CMD_STOP,
    CMD_TILT_DOWN,
    CMD_TILT_UP,
    DemoLoopSource,
    InjectedCommandSource,
    command_name,
)


MODE_CALIBRATE_CLAW = 0
MODE_DEMO_LOOP = 1
MODE_CALIBRATE_PAN = 2
MODE_CALIBRATE_TILT = 3

# C-1.2.5 starts from calibration. After freezing open/close angles,
# switch to MODE_DEMO_LOOP for the stable execution baseline.
RUN_MODE = MODE_DEMO_LOOP


def execute_command(rig, command):
    print("CMD -> " + command_name(command))

    if command == CMD_TILT_UP:
        rig.tilt_up_step()
    elif command == CMD_TILT_DOWN:
        rig.tilt_down_step()
    elif command == CMD_PAN_LEFT:
        rig.pan_left_step()
    elif command == CMD_PAN_RIGHT:
        rig.pan_right_step()
    elif command == CMD_CLAW_OPEN:
        rig.claw_open()
    elif command == CMD_CLAW_CLOSE:
        rig.claw_close()
    elif command == CMD_CENTER:
        rig.center_all()
    elif command == CMD_DEMO_LOOP_START:
        print("CMD -> DEMO_LOOP_START (loop armed)")
    elif command == CMD_STOP:
        print("CMD -> STOP (no-op in C-1.2.5)")


def run_calibration_mode(rig):
    print("MODE -> CALIBRATE_CLAW")
    print("CAL -> scan angles {}".format(CLAW_CALIBRATION_ANGLES))
    rig.center_all()

    while True:
        for angle in CLAW_CALIBRATION_ANGLES:
            print("CAL -> CLAW angle={}".format(angle))
            rig.claw_to_angle(angle)
            time.sleep_ms(CLAW_CALIBRATION_DELAY_MS)


def run_pan_calibration_mode(rig):
    print("MODE -> CALIBRATE_PAN")
    print("CAL -> software sign: PAN+ = LEFT, PAN- = RIGHT")
    print("CAL -> scan angles {}".format(PAN_CALIBRATION_ANGLES))
    rig.center_all()

    while True:
        for angle in PAN_CALIBRATION_ANGLES:
            print("CAL -> PAN angle={}".format(angle))
            rig.pan_to_angle(angle)
            time.sleep_ms(PAN_CALIBRATION_DELAY_MS)


def run_tilt_calibration_mode(rig):
    print("MODE -> CALIBRATE_TILT")
    print("CAL -> software sign: TILT+ = DOWN, TILT- = UP")
    print("CAL -> scan angles {}".format(TILT_CALIBRATION_ANGLES))
    rig.center_all()

    while True:
        for angle in TILT_CALIBRATION_ANGLES:
            print("CAL -> TILT angle={}".format(angle))
            rig.tilt_to_angle(angle)
            time.sleep_ms(TILT_CALIBRATION_DELAY_MS)


def run_demo_mode(rig):
    print("MODE -> DEMO_LOOP")
    rig.center_all()

    injected_source = InjectedCommandSource()
    demo_source = DemoLoopSource(LOOP_PAUSE_MS)

    while True:
        now_ms = millis()
        command = injected_source.next_command(now_ms)
        if command is None:
            command = demo_source.next_command(now_ms)

        if command is not None:
            execute_command(rig, command)

        time.sleep_ms(20)


rig = ActuatorRig()

if RUN_MODE == MODE_CALIBRATE_CLAW:
    run_calibration_mode(rig)
elif RUN_MODE == MODE_CALIBRATE_PAN:
    run_pan_calibration_mode(rig)
elif RUN_MODE == MODE_CALIBRATE_TILT:
    run_tilt_calibration_mode(rig)
else:
    run_demo_mode(rig)
