#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"

source "$ROOT/use_cleanscout_pi.sh"
"$ROOT/clean_ros_sessions.sh"

nohup bash -lc 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh; roslaunch clbrobot bench_full_stack.launch use_rviz:=false' >/tmp/c232_bench_launch.log 2>&1 </dev/null &

sleep 8

printf '\n[bench] rostopic list\n'
rostopic list || true

printf '\n[bench] rostopic hz /scan\n'
timeout 8 rostopic hz /scan || true

printf '\n[bench] rostopic hz /imu/data\n'
timeout 8 rostopic hz /imu/data || true

printf '\n[bench] stack launched\n'
