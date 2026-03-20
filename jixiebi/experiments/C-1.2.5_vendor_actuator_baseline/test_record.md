# C-1.2.5 Vendor Actuator Baseline Test Record

## 1. Baseline Source

- Source template:
  `J-jixiebi/introduction and examples/07 梦飞openmv4_大底座视觉识别追踪云台例程/07 蓝牙&wifi图传app控制AI视觉追踪综合案例`
- Runtime baseline uses:
  - `Servo(3)` pan
  - `Servo(4)` tilt
  - `Servo(1)` claw
- Vendor snapshots are preserved before any modification.

## 2. Frozen Runtime Defaults

- `PAN_CENTER_DEG = 0`
- `TILT_CENTER_DEG = -30`
- `PAN_STEP_DEG = 2`
- `TILT_STEP_DEG = 2`
- `SERVO_DELAY_MS = 200`
- `LOOP_PAUSE_MS = 1000`
- `CLAW_CLOSE_SEED = 50`
- `CLAW_OPEN_ANGLE = -30` (seed, pending hardware freeze)
- `CLAW_CLOSE_ANGLE = 50` (seed, pending hardware freeze)
- `CLAW_CALIBRATION_ANGLES = (-60, -30, 0, 20, 35, 50, 65, 80)`

## 3. Current Mode Policy

- Default runtime mode: `MODE_CALIBRATE_CLAW`
- After hardware confirmation of claw open/close:
  - update `CLAW_OPEN_ANGLE`
  - update `CLAW_CLOSE_ANGLE`
  - switch `RUN_MODE` to `MODE_DEMO_LOOP`

## 4. Calibration Record

- `-60`:
- `-30`:
- `0`:
- `20`:
- `35`:
- `50`:
- `65`:
- `80`:

Final frozen values:

- `CLAW_OPEN_ANGLE =`
- `CLAW_CLOSE_ANGLE =`

## 5. Demo Loop Record

Expected loop:

1. `CENTER`
2. `TILT_UP x5`
3. `TILT_DOWN x10`
4. `CENTER`
5. `PAN_LEFT x5`
6. `PAN_RIGHT x10`
7. `CENTER`
8. `CLAW_CLOSE`
9. `CLAW_OPEN`

Observed result:

- Pan left/right:
- Tilt up/down:
- Claw close:
- Claw open:
- Center:
- 3-minute repeat stability:

## 6. Current Conclusion

- New vendor actuator baseline created: `YES`
- Runtime still depends on Bluetooth hardware: `NO`
- Vision / tracking path mixed into this round: `NO`
- Ready for next round F411 command-source takeover:
  - `PENDING HARDWARE VALIDATION`
