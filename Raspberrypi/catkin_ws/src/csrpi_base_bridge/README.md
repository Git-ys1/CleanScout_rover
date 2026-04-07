# csrpi_base_bridge

`csrpi_base_bridge` is the Raspberry Pi side transition bridge for `C-2.2.6B`.

## Purpose

- keep one persistent serial connection to the UNO base controller
- wait for `CSR_UNO_READY`
- subscribe to `/cmd_vel`
- continuously send `CMD,<vx>,<vy>,<wz>` frames
- publish raw serial and parsed encoder debug topics for later ROS integration

## Current scope

- device: `/dev/csr_uno`
- baudrate: `115200`
- bridge publish rate: `20 Hz`
- input topic: `/cmd_vel`
- debug topics:
  - `/csr_base/raw_serial_line`
  - `/csr_base/encoder_debug`
  - `/csr_base/pid_debug`
  - `/csr_base/bridge_status`

This package is intentionally small and does not publish `/odom`, start EKF, or start navigation.

## Run

```bash
source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/devel/setup.bash
rosrun csrpi_base_bridge base_bridge.py
```

Then publish a test velocity:

```bash
rostopic pub /cmd_vel geometry_msgs/Twist '{linear: {x: 0.10, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' -r 1
```

## Notes

- The bridge keeps sending the latest velocity command even if `/cmd_vel` is quiet.
- If serial drops, the node closes the port, publishes bridge status, and retries.
- `READY`, `ACK`, `ENC`, `PID`, and `ERR` are all forwarded to ROS debug topics.
