#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 5 ]; then
  printf '%s\n' "用法: ./send_nav_cmd.sh vx [vy] [wz] [seconds] [topic]"
  printf '%s\n' "示例: ./send_nav_cmd.sh 0.08 0 0 2 /cmd_vel_nav"
  exit 2
fi

VX="$1"
VY="${2:-0}"
WZ="${3:-0}"
SECONDS="${4:-2}"
TOPIC="${5:-/cmd_vel_nav}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${SCRIPT_DIR}/use_cleanscout_pc.sh" ]; then
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/use_cleanscout_pc.sh"
fi

printf '%s\n' "[send-nav-cmd] topic=${TOPIC} vx=${VX} vy=${VY} wz=${WZ} duration=${SECONDS}s"

timeout "${SECONDS}s" rostopic pub -r 10 "${TOPIC}" geometry_msgs/Twist \
  "{linear: {x: ${VX}, y: ${VY}, z: 0.0}, angular: {x: 0.0, y: 0.0, z: ${WZ}}}" || true

printf '%s\n' "[send-nav-cmd] done"
