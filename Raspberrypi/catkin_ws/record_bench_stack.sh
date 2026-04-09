#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT/bags"

mkdir -p "$OUT_DIR"

export ROS_MASTER_URI="http://127.0.0.1:11311"
export ROS_IP="127.0.0.1"
export ROS_HOSTNAME="127.0.0.1"

source /opt/ros/noetic/setup.bash
source "$ROOT/devel/setup.bash"

rosbag record -O "$OUT_DIR/bench_stack_${STAMP}.bag" /scan /imu/data /tf /csr_base/raw_serial_line /csr_base/encoder_debug /csr_base/pid_debug /csr_base/bridge_status /cmd_vel
