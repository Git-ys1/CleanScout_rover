#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"

source "$ROOT/use_cleanscout_pi.sh"

OUT_DIR="$(rospack find clbrobot)/maps"
MAP_NAME="${1:-406}"

mkdir -p "$OUT_DIR"

rosrun map_server map_saver -f "$OUT_DIR/$MAP_NAME"

printf 'saved map:\n%s.pgm\n%s.yaml\n' "$OUT_DIR/$MAP_NAME" "$OUT_DIR/$MAP_NAME"
