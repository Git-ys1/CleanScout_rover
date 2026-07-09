# C-5.0.1 OrangePi YOLO11 Mechanical Arm Tracking Demo

This directory is the first non-ROS prototype for visual tracking on Orange Pi 5 Max.

## Safety Defaults

- `yolo_arm_track.py` defaults to `--dry_run true`.
- Arm output is disabled unless `--enable_arm` is provided.
- Real serial output requires both `--enable_arm` and `--dry_run false`.
- If real serial mode reports `No module named serial`, install pyserial with `~/rk3588_ai/rknn_lite_env/bin/python3 -m pip install pyserial`.
- Do not run real arm output until the lower controller is connected and single-joint yaw/pitch tests are confirmed.

## Current Default Protocol

The current repository mechanical-arm STM32 self-developed entry is `firmware/mechanical_arm_controller`.
`firmware/mechanical_arm_official_baseline` remains the frozen vendor/reference baseline.

C-5.1.2 freezes the OrangePi mechanical-arm control entrance to OpenRF1 USART3 / Bluetooth serial H6:

```text
OrangePi CH340 TX -> OpenRF1 RX3 / PB11
OrangePi CH340 RX <- OpenRF1 TX3 / PB10
OrangePi CH340 GND <-> OpenRF1 GND
baudrate: 115200 8N1
current board device: /dev/ttyUSB0, VID:PID=1A86:7523
```

USART2 / user serial H5 is reserved for future Raspberry Pi chassis control and must not be used as the OrangePi arm entrance.

The verified command format remains the official bus-servo ASCII text protocol:

```text
#000P1500T0200!
#003P1500T0200!
#000PDST!
#003PDST!
```

The ROS2 reference binary frames from `car_base.cpp` are kept as a disabled compatibility backend only. They are not the default because the currently frozen mechanical-arm baseline parses text commands.

## Dry-Run Checks

```bash
cd ~/rk3588_ai/arm_tracking_demo
~/rk3588_ai/rknn_lite_env/bin/python3 tools/scan_serial.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_arm_driver_dryrun.py --print_cmd
```

Expected dry-run command:

```text
{#000P1500T0200!#003P1500T0200!}
#000PDST!
#003PDST!
```

The first tracking loop owns only Servo000 (yaw) and Servo003 (pitch).
It must not rewrite Servo001/002/004/005 on every video frame.

Before real tracking, the default configuration moves Servo001/002 to the
verified conservative forward pose (`1350/1750`) over 3 seconds and waits
4 seconds for the camera load to settle. Use `--prepare_pose false` to skip it.

## Bus-Servo Readback Probe

Full protocol table: `../../../docs/VERIFY/C-5.0.2_arm_bus_servo_command_table.md`.

Use the official bus-servo read commands before blaming the visual-servo code:

```bash
cd ~/rk3588_ai/arm_tracking_demo
~/rk3588_ai/rknn_lite_env/bin/python3 tools/bus_servo_probe.py \
  --serial_port /dev/ttyUSB0 \
  --read position \
  --ids 0-5
```

Read ID, version, position, temperature, and voltage:

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/bus_servo_probe.py \
  --serial_port /dev/ttyUSB0 \
  --read all \
  --ids 0-5
```

Verified on 2026-06-11 through `/dev/ttyUSB0`:

- `#000PVER!` returned `#000P Servo V20240126G!`.
- `#000PRAD!` returned positions such as `#000P1500!`.
- Servo000 moved to 1550, 1450, and back to 1500; every position was read back correctly.

Only one process may own `/dev/ttyUSB0`. The driver and probe request an exclusive
Linux serial lock so a tracker/probe pair cannot consume each other's replies.

## Visual Dry-Run

List all classes recognized by the current YOLO model:

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 yolo_arm_track.py --list_classes
```

The default target class is `any`, meaning any class recognized by that model.
It does not mean arbitrary objects outside the model's training classes.

```bash
cd ~/rk3588_ai/arm_tracking_demo
~/rk3588_ai/rknn_lite_env/bin/python3 yolo_arm_track.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 0 \
  --track_class person \
  --dry_run true \
  --print_cmd \
  --max_frames 200
```

This shows target center, errors, and yaw/pitch commands. It does not send arm commands unless `--enable_arm` is also set.

## First Real-Arm Sequence

Run only after the lower controller serial port is physically connected and visible in `tools/scan_serial.py`.

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_one_joint_yaw.py \
  --serial_port /dev/ttyUSB0 \
  --enable_arm \
  --dry_run false \
  --yaw 0.03
```

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_one_joint_pitch.py \
  --serial_port /dev/ttyUSB0 \
  --enable_arm \
  --dry_run false \
  --pitch 1.23
```

Only after both axes move in the expected direction should closed-loop tracking be enabled.

## Hotkeys

- `q` or `ESC`: quit.
- `s`: save snapshot if `--snapshot_path` is configured.
- `space`: pause or resume arm output while vision continues.
- `r`: reset yaw/pitch command to configured initial values.

## Files

- `arm_driver.py`: only module allowed to talk to the lower controller.
- `visual_servo.py`: center-error to yaw/pitch P/PID controller.
- `target_selector.py`: detection filtering and target selection.
- `yolo_arm_track.py`: camera, YOLO11 RKNN, selection, overlay, optional arm output.
- `tools/scan_serial.py`: serial-port inventory.
- `tools/bus_servo_probe.py`: bus-servo ASCII send/read probe.
- `tools/test_arm_driver_dryrun.py`: text/binary payload smoke test.
- `tools/test_one_joint_yaw.py`: yaw-only first real movement test.
- `tools/test_one_joint_pitch.py`: pitch-only first real movement test.
- `tools/test_camera_arm_motion.py`: identify real joint motion from end-camera displacement.
- `tools/test_visual_servo_motion.py`: deterministic real-hardware visual-servo chain test.
