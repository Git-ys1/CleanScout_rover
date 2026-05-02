# Multi Function Demo Test

This document is for local testing of the current multi-function demo node on Raspberry Pi.

## Current demo contents

The current demo launch starts:

1. fan + lid interlock bridge
2. edge relay bridge (optional)

Launch file:

`/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/demo/multi_function_demo.launch`

## Before testing

### 1. Build workspace

```bash
cd /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
catkin_make
```

### 2. Start pigpio

If systemd service exists:

```bash
sudo systemctl start pigpiod
```

If systemd service does not exist:

```bash
sudo pigpiod
```

### 3. Load ROS environment

In every shell:

```bash
cd /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
source ./use_cleanscout_pi.sh
```

## Start demo launch

### Demo without edge relay

```bash
roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/demo/multi_function_demo.launch
```

### Demo with edge relay

```bash
roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/demo/multi_function_demo.launch \
  enable_edge_relay:=true \
  edge_url:=ws://10.44.63.190:3000/edge/ros \
  edge_device_id:=csrpi-001 \
  edge_device_token:=YOUR_TOKEN
```

## Fan bridge functional test

### Open fan system

```bash
rostopic pub -1 /fan_a/pwm_percent std_msgs/Float32 "data: 35.0"
rostopic pub -1 /fan_b/pwm_percent std_msgs/Float32 "data: 35.0"
rostopic pub -1 /fans/enable std_msgs/Bool "data: true"
```

Expected behavior:

1. lid opens first
2. relay enables after lid settle
3. both fans start blowing

### Stop fan system

```bash
rostopic pub -1 /fans/enable std_msgs/Bool "data: false"
```

Expected behavior:

1. both PWM outputs go to zero first
2. relay disables
3. lid closes

## Feedback observation

Open extra terminals and observe:

```bash
rostopic echo /fan_a/rpm
rostopic echo /fan_b/rpm
rostopic echo /fan_lid/state
rostopic echo /fans/state_summary
```

Optional raw FG diagnostics:

```bash
rostopic echo /fan_a/fg_in_rpm
rostopic echo /fan_a/fg_out_rpm
rostopic echo /fan_b/fg_in_rpm
rostopic echo /fan_b/fg_out_rpm
```

## Edge relay test

When edge relay is enabled, confirm that the node is online and logs no websocket auth failure.

Suggested checks:

```bash
rosnode list | grep edge_relay
```

If needed, inspect launch output directly in the terminal where demo launch runs.

## Minimal pass criteria

1. demo launch starts without immediate crash
2. `/fans/enable=true` causes lid open -> relay on -> fan pwm active
3. `/fans/enable=false` causes pwm off -> relay off -> lid close
4. `/fan_a/rpm` and `/fan_b/rpm` show non-zero values while fans are spinning
5. state topics update consistently

## If test fails, report these first

1. launch terminal full output
2. whether pigpio daemon was started successfully
3. whether lid moved on enable
4. whether relay clicked on enable
5. whether fan A/B actually spun
6. `/fan_a/rpm` and `/fan_b/rpm` values
7. `/fans/state_summary` output
