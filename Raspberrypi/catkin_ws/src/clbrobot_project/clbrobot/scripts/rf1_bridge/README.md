# OpenRF1 USB Bridge Smoke Test

This directory contains the Raspberry Pi side non-ROS smoke test for the current OpenRF1 USB serial contract.

## Device

- preferred device: `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`
- fallback device: `/dev/ttyUSB1`
- USB chip: `1a86:7523` (`CH341`)

## Protocol freeze for this phase

- baudrate: `115200`
- command cycle target: `50 Hz`
- telemetry cycle target: `10 Hz`
- control command: `W,a,b,c,d`
- debug commands: `M,ch,pwm`, `E,ch`, `STOP`

## Run

```bash
source /opt/ros/noetic/setup.bash
python3 /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/scripts/rf1_bridge/openrf1_smoketest.py
```

For the `C-3.2.0` minimal bridge baseline, use the continuous-send smoke test:

```bash
source /opt/ros/noetic/setup.bash
python3 /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/scripts/rf1_bridge/openrf1_min_bridge_smoketest.py
```

This variant keeps sending `W,a,b,c,d` at `50 Hz` for a short window, which matches the OpenRF1 board timeout contract more closely than a single-shot command test.

## Current note

This is intentionally a non-ROS test. The goal is to prove Raspberry Pi to OpenRF1 USB serial communication before replacing the old ROS serial base path.
