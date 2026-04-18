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
- `TILT_CENTER_DEG = 85`
- `PAN_STEP_DEG = 2`
- `TILT_STEP_DEG = 2`
- `SERVO_DELAY_MS = 200`
- `LOOP_PAUSE_MS = 1000`
- `CLAW_CLOSE_SEED = 50`
- `PAN_MIN_DEG = -90`
- `PAN_MAX_DEG = 90`
- `TILT_MIN_DEG = 0`
- `TILT_MAX_DEG = 90`
- `CLAW_OPEN_ANGLE = -60`
- `CLAW_CLOSE_ANGLE = 40`
- `CLAW_CALIBRATION_ANGLES = (-60, -30, 0, 20, 30, 40)`

## 3. Current Mode Policy

- Default runtime mode: `MODE_DEMO_LOOP`
- Calibration modes remain available for re-test:
  - `MODE_CALIBRATE_CLAW`
  - `MODE_CALIBRATE_PAN`
  - `MODE_CALIBRATE_TILT`

## 4. Calibration Record

- `-60`: 完全张开状态
- `-30`:
- `0`: 基本合上，间距为2.4cm左右，2.4cm状态对中间无力作用
- '10': 比较与0而言，常态间距为1.8cm，但实际对于2cm的物块无力作用
- `20`: 以2cm的物块为分界吧，常态观察距离为1cm左右，实际对2cm的物块产生力作用，但实际上无法夹住
- `30`: 常态观察距离为0.2cm左右，实际可以夹起2cm、1cm的物块，但对0.6cm的物体无法夹的很紧
- `40`: 已经可以对0.6cm夹的很紧，后续挡位会使得舵机无法到达目标值而发烫，当前状态无发热，建议定为上界

Final frozen values:

- `CLAW_OPEN_ANGLE = -60`
- `CLAW_CLOSE_ANGLE = 40`

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

- Pan left/right: 正常
- Tilt up/down: 正常
- Claw close: 正常
- Claw open: 正常
- Center: 正常
- 3-minute repeat stability: 正常

## 6. Pan Calibration Record

Software sign:

- `PAN +` = left
- `PAN -` = right

Suggested scan list:

- `PAN_CALIBRATION_ANGLES = (-90, -60, -30, 0, 30, 60, 90)`

Observed result:

- `-90`: 右转 90 度，朝右
- `0`: 正前中位
- `90`: 左转 90 度，朝左

Frozen result:

- `PAN_MIN_DEG = -90`
- `PAN_MAX_DEG = 90`
- `PAN_CENTER_DEG = 0`

## 7. Tilt Calibration Record

Software sign:

- `TILT 0` = up boundary
- `TILT +` = down

Suggested scan list:

- `TILT_CALIBRATION_ANGLES = (0, 10, 20, 30, 60, 85, 90)`

Observed result:

- `0`: 上方边界，板面/摄像头朝向已接近向上
- `10`:
- `20`:
- `30`:
- `60`:
- `85`: 默认运行位
- `90`: 朝地边界，下方极限

Frozen result:

- `TILT_MIN_DEG = 0`
- `TILT_MAX_DEG = 90`
- `TILT_CENTER_DEG = 85`

## 8. Current Conclusion

- New vendor actuator baseline created: `YES`
- Runtime still depends on Bluetooth hardware: `NO`
- Vision / tracking path mixed into this round: `NO`
- Ready for next round F411 command-source takeover:
  - `YES`
