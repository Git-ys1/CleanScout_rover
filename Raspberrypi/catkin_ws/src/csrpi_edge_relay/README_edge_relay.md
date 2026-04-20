# Edge Relay

## Purpose

`edge-relay` is the second transport added in `C-3.2.4`.

It does not replace the current local rosbridge chain.

The architecture is:

- local chain: `backend -> rosbridge -> ROS -> OpenRF1`
- cloud chain: `backend <-WSS-> edge-relay(Pi) -> ROS -> OpenRF1`

## Current endpoint

- https api: `https://api.hzhhds.top`
- websocket relay: `ws://10.22.7.190:3000/edge/ros`

For current local V-line backend testing, use:

- `ws://10.22.7.190:3000/edge/ros`

## Current behavior

- Pi actively creates a long-lived WSS connection
- first frame is `hello`
- heartbeat every `5s`
- telemetry summary uploads `odom`, `imu`, and `scanSummary`
- backend `manual_control` is converted into local `/cmd_vel`
- backend `stop` immediately publishes zero velocity

## Current ROS interfaces

- publish:
  - `/cmd_vel`
- subscribe:
  - `/odom`
  - `/imu/data`
  - `/scan`

## Current safety limits

- `vx`: `[-0.20, 0.20] m/s`
- `vy`: `[-0.15, 0.15] m/s`
- `wz`: `[-0.35, 0.35] rad/s`
- default hold: `400 ms`
- cmd repeat rate: `10 Hz`

## Environment variables

- `EDGE_RELAY_ENABLED`
- `EDGE_RELAY_URL`
- `EDGE_DEVICE_ID`
- `EDGE_DEVICE_TOKEN`
- `EDGE_HEARTBEAT_MS`
- `EDGE_ODOM_HZ`
- `EDGE_IMU_HZ`
- `EDGE_SCAN_HZ`
- `EDGE_CMD_REPEAT_HZ`
- `EDGE_CMD_DEFAULT_HOLD_MS`
- `EDGE_RECONNECT_DELAY_MS`

## V-line local backend profile

Current V-line guidance says local edge tests should use the backend `public-edge` profile instead of `local-lan`.

Key points:

- backend uses `ROS_TRANSPORT=edge-relay`
- backend exposes `/edge/ros`
- Pi connects actively to the backend websocket endpoint
- Pi token must match the backend seeded edge device token
- local test first, cloud switch later

## Run

```bash
source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh
/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/run_edge_relay.sh
```

## Cleanup

```bash
/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/clean_edge_relay_sessions.sh
```

## Current limitation

The relay needs a Python websocket client package on the Pi runtime.

If `python3-websocket` is not installed, the relay node will not be able to connect and will log a dependency error.
