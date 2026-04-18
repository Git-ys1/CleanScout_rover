#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"

source "$ROOT/use_cleanscout_pi.sh"
"$ROOT/clean_ros_sessions.sh"

echo "[start] launching mapping stack in foreground"
roslaunch "$ROOT/src/clbrobot_project/clbrobot/launch/slam/lidar_slam_pi.launch"
