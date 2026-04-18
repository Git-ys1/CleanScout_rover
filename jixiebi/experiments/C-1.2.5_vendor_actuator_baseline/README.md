# C-1.2.5 Vendor Actuator Baseline

## 1. Goal

This experiment resets the `J` line execution baseline to the vendor
`07 蓝牙&wifi图传app控制AI视觉追踪综合案例` template, but only keeps the actuator layer:

- `Servo(3)` pan
- `Servo(4)` tilt
- `Servo(1)` claw
- single-byte command-state organization

This round does **not** include:

- face / YOLO / color recognition
- full grasp logic
- `C↔J` communication
- live Bluetooth dependency

## 2. Files

- `vendor_main_snapshot.py`: raw vendor control baseline
- `vendor_pid_snapshot.py`: raw vendor PID baseline
- `vendor_ubluetooth_snapshot.py`: raw vendor command-state baseline
- `main.py`: current execution-baseline entry
- `actuator.py`: gimbal / claw primitives
- `command_source.py`: local command-source abstraction
- `pid.py`: carried over for future visual baseline reuse

## 3. Current Modes

- `MODE_CALIBRATE_CLAW`
  - default for the first bring-up
  - scans the claw through frozen angle candidates
- `MODE_DEMO_LOOP`
  - actuator-only demo loop
  - runs center / tilt / pan / claw actions in a repeatable sequence

## 4. Deployment

Board-side minimum package:

- `main.py`
- `actuator.py`
- `command_source.py`
- `pid.py`

If you want to keep the vendor snapshots on the board for inspection, they can be copied too, but they are not runtime dependencies.

## 5. Next Step

Freeze real `CLAW_OPEN_ANGLE` / `CLAW_CLOSE_ANGLE` from hardware observation first.
Only after that should `RUN_MODE` switch from `MODE_CALIBRATE_CLAW` to `MODE_DEMO_LOOP`.
