#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi"
OUT_DIR="$ROOT/maps"
MAP_NAME="${1:-lab_map_001}"

mkdir -p "$OUT_DIR"

export ROS_MASTER_URI="${ROS_MASTER_URI:-http://127.0.0.1:11311}"
export ROS_IP="${ROS_IP:-127.0.0.1}"
export ROS_HOSTNAME="${ROS_HOSTNAME:-127.0.0.1}"

source /opt/ros/noetic/setup.bash

rosrun map_server map_saver -f "$OUT_DIR/$MAP_NAME"

printf 'saved map:\n%s.pgm\n%s.yaml\n' "$OUT_DIR/$MAP_NAME" "$OUT_DIR/$MAP_NAME"
