# C-1.2.6 Vendor Vision Grasp Baseline

## Runtime Files

Deploy these files to the OpenMV board for the C-1.2.6 runtime:

- `main.py`
- `actuator.py`
- `vision.py`
- `pid.py`

Do not deploy the snapshot files as runtime entrypoints.

## Snapshot Files

These files are preserved as vendor evidence only:

- `vendor_main_snapshot.py`
- `vendor_main_yellow_snapshot.py`
- `vendor_camera_lcd_selftest_snapshot.py`

## Baseline Freeze

Runtime actuator limits are inherited from C-1.2.5:

- `PAN_CENTER_DEG = 0`
- `PAN_MIN_DEG = -90`
- `PAN_MAX_DEG = 90`
- `TILT_CENTER_DEG = 85`
- `TILT_MIN_DEG = 0`
- `TILT_MAX_DEG = 90`
- `CLAW_OPEN_ANGLE = -60`
- `CLAW_CLOSE_ANGLE = 40`

Spatial sign convention:

- `PAN +` = left
- `PAN -` = right
- `TILT 0` = up boundary
- `TILT 90` = down / nose-to-ground boundary

## Current Runtime Scope

This baseline does:

- camera capture
- yellow target tracking
- PID-based pan/tilt tracking
- grasp -> drop -> reset state machine
- optional color sorting toggle in the same state machine

This baseline does not do:

- F411联调
- WAIT_PICK_WINDOW / PICK_WINDOW
- Wi-Fi图传
- 蓝牙控制
- 小车底盘联动

## State Machine

- `SCAN`
- `TRACK`
- `APPROACH_READY`
- `GRAB`
- `DROP`
- `RESET`

Default search pose:

- `pan = 0`
- `tilt = 85`
- `claw = open`

## Bring-up Order

1. Verify imports and sensor start.
2. Verify `center_pose()` returns to `pan=0, tilt=85, claw=open`.
3. Verify yellow-only tracking.
4. Verify single-color grasp/drop/reset.
5. Enable color sorting only after yellow path is stable.
