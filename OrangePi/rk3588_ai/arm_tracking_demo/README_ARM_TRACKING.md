# C-5.0.1 OrangePi YOLO11 Mechanical Arm Tracking Demo

This directory is the first non-ROS prototype for visual tracking on Orange Pi 5 Max.

## Safety Defaults

- `yolo_arm_track.py` defaults to `--dry_run true`.
- Arm output is disabled unless `--enable_arm` is provided.
- Real serial output requires both `--enable_arm` and `--dry_run false`.
- The current OrangePi Python environment does not have `pyserial`; real serial mode will fail until `pyserial` is installed in `~/rk3588_ai/rknn_lite_env`.
- Do not run real arm output until the lower controller is connected and single-joint yaw/pitch tests are confirmed.

## Current Default Protocol

The current repository mechanical-arm STM32 baseline is `firmware/mechanical_arm_official_baseline`.
Its verified command format is the official PWM-servo text protocol:

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
#000P1500T0200!#003P1500T0200!
#000PDST!
#003PDST!
```

## Visual Dry-Run

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
  --serial_port /dev/ttyS7 \
  --enable_arm \
  --dry_run false \
  --yaw 0.03
```

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_one_joint_pitch.py \
  --serial_port /dev/ttyS7 \
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
- `tools/test_arm_driver_dryrun.py`: text/binary payload smoke test.
- `tools/test_one_joint_yaw.py`: yaw-only first real movement test.
- `tools/test_one_joint_pitch.py`: pitch-only first real movement test.
