# csrpi_base_bridge

`csrpi_base_bridge` is the Raspberry Pi side wheel-target bridge for `C-2.2.7`.

## Purpose

- keep one persistent serial connection to the UNO base controller
- wait for `CSR_UNO_READY`
- keep one persistent serial connection to the UNO base controller
- wait for `CSR_UNO_READY`
- continuously send `W,w1,w2,w3,w4` frames
- publish raw serial and parsed encoder debug topics for later ROS integration

## Current scope

- device: `/dev/csr_uno`
- baudrate: `115200`
- bridge publish rate: `20 Hz`
- current command topic: `/csr_base/wheel_targets`
- debug topics:
  - `/csr_base/raw_serial_line`
  - `/csr_base/encoder_debug`
  - `/csr_base/pid_debug`
  - `/csr_base/bridge_status`

This package is intentionally small and does not publish `/odom`, start EKF, or start navigation.
`cmdvel_to_wheels.py` is only a stage-two skeleton and is not the default control entry yet.

## Run

```bash
source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/devel/setup.bash
rosrun csrpi_base_bridge wheel_bridge.py
```

Then publish a manual wheel target for validation:

```bash
rostopic pub /csr_base/wheel_targets std_msgs/Int32MultiArray '{data: [100, 100, 100, 100]}' -r 1
```

## Notes

- The bridge keeps sending the latest wheel target even if the input topic is quiet.
- If serial drops, the node closes the port, publishes bridge status, and retries.
- `READY`, `ACK:W`, `ENC`, `PID`, and `ERR` are all forwarded to ROS debug topics.
- `CMD,<vx>,<vy>,<wz>` is no longer used as the active Raspberry Pi to UNO protocol.
