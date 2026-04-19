#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"

source "$ROOT/use_cleanscout_pi.sh"
"$ROOT/clean_ros_sessions.sh"

nohup bash -lc 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh; roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/slam/lidar_slam_pi.launch' >/tmp/c233_slam.log 2>&1 </dev/null &

sleep 10

printf '\n[c233] rostopic list\n'
rostopic list || true

printf '\n[c233] rostopic hz /scan\n'
timeout 8 rostopic hz /scan || true

printf '\n[c233] rostopic hz /imu/data\n'
timeout 8 rostopic hz /imu/data || true

printf '\n[c233] rostopic echo -n 1 /odom\n'
timeout 8 rostopic echo -n 1 /odom || true

printf '\n[c233] tf check reminder: inspect odom->base_footprint/base_link, base_footprint->imu_link, base_link->laser in RViz\n'
