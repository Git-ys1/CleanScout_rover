#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT/bags"

mkdir -p "$OUT_DIR"

source "$ROOT/use_cleanscout_pi.sh"

rosbag record -O "$OUT_DIR/bench_stack_${STAMP}.bag" /scan /imu/data /tf /csr_base/raw_serial_line /csr_base/encoder_debug /csr_base/pid_debug /csr_base/bridge_status /cmd_vel
