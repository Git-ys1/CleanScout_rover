#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"

pkill -9 -f roscore || true
pkill -9 -f rosmaster || true
pkill -9 -f roslaunch || true
pkill -9 -f rplidarNode || true
pkill -9 -f mpu6050_node.py || true
pkill -9 -f wheel_bridge.py || true

export ROS_MASTER_URI="http://127.0.0.1:11311"
export ROS_IP="127.0.0.1"
export ROS_HOSTNAME="127.0.0.1"

source /opt/ros/noetic/setup.bash
source "$ROOT/devel/setup.bash"

nohup bash -lc 'export ROS_MASTER_URI=http://127.0.0.1:11311 ROS_IP=127.0.0.1 ROS_HOSTNAME=127.0.0.1; source /opt/ros/noetic/setup.bash; source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/devel/setup.bash; rosmaster --core -p 11311 -w 3' >/tmp/c232_master.log 2>&1 </dev/null &
sleep 2

nohup bash -lc 'export ROS_MASTER_URI=http://127.0.0.1:11311 ROS_IP=127.0.0.1 ROS_HOSTNAME=127.0.0.1; source /opt/ros/noetic/setup.bash; source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/devel/setup.bash; roslaunch clbrobot bench_full_stack.launch use_rviz:=false' >/tmp/c232_bench_launch.log 2>&1 </dev/null &

sleep 8

printf '\n[bench] rostopic list\n'
rostopic list || true

printf '\n[bench] rostopic hz /scan\n'
timeout 8 rostopic hz /scan || true

printf '\n[bench] rostopic hz /imu/data\n'
timeout 8 rostopic hz /imu/data || true

printf '\n[bench] stack launched\n'
