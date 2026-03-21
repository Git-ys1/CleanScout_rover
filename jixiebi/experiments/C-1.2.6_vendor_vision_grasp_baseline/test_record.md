# C-1.2.6 Vendor Vision Grasp Baseline Test Record

## 1. Baseline Source

- Primary vendor source: `J-jixiebi/introduction and examples/main.py`
- Yellow-only backup: `main.py~RFb594dd.TMP`
- Camera/LCD selftest backup: `main.py~RFb291ce.TMP`
- PID source actually used: `jixiebi/experiments/C-1.2.5_vendor_actuator_baseline/pid.py`
- PID hash check against local vendor copy: `MATCHED`

## 2. Frozen Actuator Boundaries From C-1.2.5

- `PAN_CENTER_DEG = 0`
- `PAN_MIN_DEG = -90`
- `PAN_MAX_DEG = 90`
- `TILT_CENTER_DEG = 85`
- `TILT_MIN_DEG = 0`
- `TILT_MAX_DEG = 90`
- `CLAW_OPEN_ANGLE = -60`
- `CLAW_CLOSE_ANGLE = 40`

## 3. Default Search Pose

- `pan = 0`
- `tilt = 85`
- `claw = open`

## 4. Motion Mapping Notes

Vendor defaults replaced by runtime mapping:

- vendor `pan_servo.angle(90, 2000)` -> `center_pose()` with `pan = 0`
- vendor `tilt_servo.angle(30, 2000)` -> `center_pose()` with `tilt = 85`
- vendor tilt clamp `[-80, 80]` -> runtime clamp `[0, 90]`
- vendor claw release/catch `-70 / 50` -> runtime `-60 / 40`

## 5. Timing Normalization

Vendor `time.sleep(2000)` / `time.sleep(1000)` style delays are treated as millisecond mistakes.
Runtime normalization:

- `CLAW_SETTLE_MS = 500`
- `LIFT_SETTLE_MS = 800`
- `DROP_SETTLE_MS = 800`
- `RESET_SETTLE_MS = 800`

## 6. State Machine Gates

### Gate1 Import / Selftest
- `main.py` import: `PENDING`
- `pid.py` import: `PENDING`
- `sensor` startup: `PENDING`
- LCD selftest snapshot checked: `PENDING`

### Gate2 Actuator Mapping
- `center_pose()` -> `pan=0, tilt=85, claw=open`: `PENDING`
- tilt clamp stays inside `0..90`: `PENDING`
- no fallback to vendor `pan=90, tilt=30`: `PENDING`

### Gate3 Yellow Visualization
- rectangle/cross overlay: `PENDING`
- state text visible: `PENDING`
- target loss returns to default search pose: `PENDING`

### Gate4 Yellow Grasp Chain
- yellow track stable: `PENDING`
- `APPROACH_READY` reached: `PENDING`
- `GRAB -> DROP -> RESET` completed: `PENDING`

### Gate5 Color Sorting
- red path: `PENDING`
- yellow path: `PENDING`
- blue path: `PENDING`

### Gate6 Stability
- 10 consecutive runs: `PENDING`
- success count: 
- failure count: 
- failure reason: 
