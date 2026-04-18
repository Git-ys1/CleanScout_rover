# RF1 Web Stack

## Purpose

This document freezes the Raspberry Pi side startup chain for `C-3.2.1`.

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
