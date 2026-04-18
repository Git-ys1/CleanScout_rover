# OpenRF1 ROS Minimal Bridge

## Purpose

This document freezes the Raspberry Pi side minimal ROS bridge for `C-3.2.0`.

The goal of this stage is only to switch the Raspberry Pi base-control baseline from the old Arduino path to the OpenRF1 USB serial path.

This stage does not restore lidar, IMU, odom, EKF, or navigation.

## Current baseline

- device priority:
  - `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`
  - `/dev/ttyUSB0`
- baudrate: `115200`
- control send rate: `50 Hz`
- serial timeout: `0.2 s`
- command format: `W,a,b,c,d`
- command unit: wheel target speed in `m/s`

## ROS nodes

### `cmdvel_to_rf1.py`

- package: `csrpi_base_bridge`
- subscribes: `/cmd_vel`
- publishes: `/rf1/wheel_target_ms`
- behavior:
  - converts `vx / vy / wz` into mecanum wheel target speeds in `m/s`
  - republishes at `50 Hz`
  - outputs zeros when `/cmd_vel` times out

### `rf1_serial_bridge.py`

- package: `csrpi_base_bridge`
- subscribes: `/rf1/wheel_target_ms`
- publishes:
  - `/rf1/ready`
  - `/rf1/raw_rx`
  - `/rf1/vel`
  - `/rf1/pwm`
  - `/rf1/enc`
  - `/rf1/dbg`
  - `/rf1/ack`
  - `/rf1/error`
  - `/rf1/status`
- behavior:
  - opens the OpenRF1 USB serial device
  - drains startup serial data without blocking on `CSR_RF1_READY`
  - continuously sends `W,a,b,c,d` at `50 Hz`
  - parses `CSR_RF1_READY`, `ACK:*`, `ERR:*`, `VEL`, `PWM`, `ENC`, `DBG`
  - sends multiple `STOP` frames on shutdown

## Launch entry

Current minimal launch entry:

```text
clbrobot/launch/bringup_rf1_min.launch
```

Run example:

```bash
source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh
roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_min.launch
```

## Why old bringup is not the baseline anymore

The old baseline depends on Arduino-era assumptions:

- `rosserial_python`
- old `/dev/clbbase` or UNO serial path
- old wheel-target protocol in `ticks/s`

OpenRF1 no longer uses that contract.

The current board contract is:

- USB serial directly to Raspberry Pi
- `W,a,b,c,d`
- wheel target speeds in `m/s`
- board-side telemetry frames such as `VEL`, `PWM`, `ENC`, `DBG`

Because of that, the old Arduino bringup path must remain historical only and should not be reused as the formal RF1 baseline.
