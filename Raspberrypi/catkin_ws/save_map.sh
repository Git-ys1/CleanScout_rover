#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${ROS_MASTER_URI:-}" ] || [ -z "${ROS_IP:-}" ]; then
  if [ -f "$ROOT/use_cleanscout_pc.sh" ]; then
    source "$ROOT/use_cleanscout_pc.sh"
  else
    source "$ROOT/use_cleanscout_pi.sh"
  fi
fi

OUT_DIR="$(rospack find clbrobot)/maps"
DEFAULT_MAP_NAME="407-$(date +%-m.%-d-%H%M)"
MAP_NAME="${1:-$DEFAULT_MAP_NAME}"

mkdir -p "$OUT_DIR"

rosrun map_server map_saver -f "$OUT_DIR/$MAP_NAME"

printf 'saved map:\n%s.pgm\n%s.yaml\n' "$OUT_DIR/$MAP_NAME" "$OUT_DIR/$MAP_NAME"
