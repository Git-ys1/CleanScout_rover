#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
  printf '%s\n' "Usage: $0 left|right [command_wz_rad_s] [turn_sec]"
  exit 2
fi

DIRECTION_NAME="$1"
COMMAND_WZ="${2:-0.20}"
TURN_SEC="${3:-3.0}"

case "${DIRECTION_NAME}" in
  left)
    DIRECTION=1
    ;;
  right)
    DIRECTION=-1
    ;;
  *)
    printf '%s\n' "Direction must be left or right"
    exit 2
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/use_cleanscout_pc.sh"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT_DIR="/tmp/cleanscout-turn-${STAMP}-${DIRECTION_NAME}"
mkdir -p "${OUTPUT_DIR}"

LSM_PID=""
BAG_PID=""

publish_stop() {
  timeout 2 rostopic pub -r 20 /cmd_vel_nav geometry_msgs/Twist \
    '{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' \
    >/dev/null 2>&1 || true
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  publish_stop
  if [ -n "${BAG_PID}" ] && kill -0 "${BAG_PID}" 2>/dev/null; then
    kill -INT "${BAG_PID}" 2>/dev/null || true
    wait "${BAG_PID}" 2>/dev/null || true
  fi
  if [ -n "${LSM_PID}" ] && kill -0 "${LSM_PID}" 2>/dev/null; then
    kill "${LSM_PID}" 2>/dev/null || true
    wait "${LSM_PID}" 2>/dev/null || true
  fi
  printf '%s\n' "[turn-calibration] artifacts: ${OUTPUT_DIR}"
  exit "${status}"
}
trap cleanup EXIT INT TERM

publish_stop

rosrun laser_scan_matcher laser_scan_matcher_odom_node \
  __name:=laser_scan_matcher_turn_calib \
  _base_frame:=base_link \
  _fixed_frame:=odom_turn_calib \
  _use_cloud_input:=false \
  _use_imu:=false \
  _use_odom:=false \
  _use_alpha_beta:=false \
  _publish_tf:=false \
  _publish_pose:=true \
  _publish_vel:=false \
  _max_linear_correction:=0.40 \
  _max_angular_correction_deg:=30.0 \
  _max_iterations:=20 \
  _max_correspondence_dist:=0.30 \
  scan:=/scan \
  pose2D:=/pose2D_turn_calib \
  >"${OUTPUT_DIR}/laser_scan_matcher.log" 2>&1 &
LSM_PID=$!

for _ in $(seq 1 50); do
  if rostopic list | grep -Fx /pose2D_turn_calib >/dev/null; then
    break
  fi
  sleep 0.1
done

if ! kill -0 "${LSM_PID}" 2>/dev/null; then
  printf '%s\n' "laser scan matcher failed to start"
  exit 1
fi

rosbag record --buffsize=256 \
  -O "${OUTPUT_DIR}/turn.bag" \
  /cmd_vel_nav /cmd_vel /rf1/wheel_target_ms /rf1/vel \
  /scan /pose2D_turn_calib /odom \
  >"${OUTPUT_DIR}/rosbag.log" 2>&1 &
BAG_PID=$!

sleep 1

rosrun csrpi_base_bridge rf1_turn_calibrator.py \
  _direction:="${DIRECTION}" \
  _command_wz:="${COMMAND_WZ}" \
  _turn_sec:="${TURN_SEC}" \
  _output:="${OUTPUT_DIR}/result.json" \
  2>&1 | tee "${OUTPUT_DIR}/calibrator.log"
