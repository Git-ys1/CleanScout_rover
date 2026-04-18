# RF1 Web Stack

## Purpose

This document freezes the Raspberry Pi side startup chain for `C-3.2.2`.

The stack is focused on local web integration, not full navigation recovery.

## Current scope

The stack provides:

- OpenRF1 USB serial bridge
- `/cmd_vel -> W,a,b,c,d` at `50 Hz`
- lightweight `/odom` integration from `/rf1/vel`
- MPU6050 standard `/imu/data`
- real RPLIDAR `/scan`
- `rosbridge_websocket` on port `9090`

## Current constraints

- OpenRF1 serial:
  - preferred device: `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`
  - fallback device: `/dev/ttyUSB0`
  - baudrate: `115200`
- RF1 safety limit for V-line first real tests:
  - `vx`: `[-0.20, 0.20] m/s`
  - `vy`: `[-0.15, 0.15] m/s`
  - `wz`: `[-0.35, 0.35] rad/s`
  - hold timeout: `400 ms`
- `use_cleanscout_pi.sh` now falls back to source-only mode if `devel/setup.bash` is missing
- current machine still relies on `/home/clbrobot/catkin_ws/devel/setup.bash` for the already-built `rplidar_ros` runtime while the source package has been migrated into the current workspace

## Entry points

- cleanup:
  - `Raspberrypi/catkin_ws/clean_rf1_web_sessions.sh`
- one-command startup:
  - `Raspberrypi/catkin_ws/run_rf1_web_stack.sh`
- launch file:
  - `Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_web.launch`

## Run

```bash
source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh
/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/run_rf1_web_stack.sh
```

## Expected topics

- `/cmd_vel`
- `/odom`
- `/imu/data`
- `/scan`
- `/rf1/vel`
- `/rf1/pwm`
- `/rf1/enc`

## rosbridge contract

- websocket url: `ws://<raspberry-pi-ip>:9090`
- local web debugging topics:
  - `/cmd_vel`
  - `/odom`
  - `/imu/data`
  - `/scan`

## RF1 serial contract

- physical link: OpenRF1 onboard USB to Raspberry Pi USB
- baudrate: `115200`
- command: `W,a,b,c,d`
- unit: wheel target speed in `m/s`
- control rate: `50 Hz`
- telemetry: `ACK`, `VEL`, `PWM`, `ENC`, `DBG`

## Current boundary

- this stage is for local rosbridge debugging only
- public network exposure is not handled in this stage
- `/odom` is still a lightweight integrator, not the final EKF chain
