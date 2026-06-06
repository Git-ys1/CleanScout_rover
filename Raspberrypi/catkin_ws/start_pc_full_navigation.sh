#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "${SCRIPT_DIR}/use_cleanscout_pc.sh" ]; then
  echo "Missing environment script: ${SCRIPT_DIR}/use_cleanscout_pc.sh" >&2
  exit 1
fi

source "${SCRIPT_DIR}/use_cleanscout_pc.sh"

START_RVIZ="${START_RVIZ:-1}"
SCAN_TOPIC="${SCAN_TOPIC:-/scan}"
IMU_TOPIC="${IMU_TOPIC:-/imu/data}"
VEL_TOPIC="${VEL_TOPIC:-/rf1/vel}"
ODOM_TOPIC="${ODOM_TOPIC:-/odom}"
MAP_FILE="${MAP_FILE:-$(rospack find clbrobot)/maps/407-5.22-2120.yaml}"
USE_LASER_SCAN_MATCHER="${USE_LASER_SCAN_MATCHER:-0}"
NAV_LAUNCH="${NAV_LAUNCH:-navigation_406_rf1_teb.launch}"
# Effective yaw lever arm used to reconstruct angular velocity from measured
# wheel linear speeds. This is independent from command-side turn tuning.
ODOM_K_M="${ODOM_K_M:-0.1987}"

wait_for_topic() {
  local topic="$1"
  echo "Waiting for ${topic} ..."
  until rostopic list 2>/dev/null | grep -Fx -- "${topic}" >/dev/null; do
    sleep 1
  done
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  if [ -n "${ODOM_PID:-}" ] && kill -0 "${ODOM_PID}" 2>/dev/null; then
    kill "${ODOM_PID}" 2>/dev/null || true
    wait "${ODOM_PID}" 2>/dev/null || true
  fi
  if [ -n "${LSM_PID:-}" ] && kill -0 "${LSM_PID}" 2>/dev/null; then
    kill "${LSM_PID}" 2>/dev/null || true
    wait "${LSM_PID}" 2>/dev/null || true
  fi
  if [ -n "${NAV_PID:-}" ] && kill -0 "${NAV_PID}" 2>/dev/null; then
    kill "${NAV_PID}" 2>/dev/null || true
    wait "${NAV_PID}" 2>/dev/null || true
  fi
  if [ -n "${RVIZ_PID:-}" ] && kill -0 "${RVIZ_PID}" 2>/dev/null; then
    kill "${RVIZ_PID}" 2>/dev/null || true
    wait "${RVIZ_PID}" 2>/dev/null || true
  fi
  exit "${status}"
}

trap cleanup EXIT INT TERM

wait_for_topic "${SCAN_TOPIC}"
wait_for_topic "${VEL_TOPIC}"

if [ "${USE_LASER_SCAN_MATCHER}" = "1" ]; then
  wait_for_topic "${IMU_TOPIC}"
  roslaunch clbrobot laser_scan_matcher_406.launch \
    scan_topic:="${SCAN_TOPIC}" \
    imu_topic:="${IMU_TOPIC}" \
    odom_out_topic:="${ODOM_TOPIC}" \
    pose_out_topic:=/pose2D_lsm &
  LSM_PID=$!
else
  echo "Starting RF1 encoder odom with ODOM_K_M=${ODOM_K_M}"
  rosrun csrpi_base_bridge rf1_vel_to_odom.py \
    _k_m:="${ODOM_K_M}" \
    _odom_frame:=odom \
    _base_frame:=base_link \
    _publish_tf:=true \
    _vel_timeout_sec:=0.5 \
    _publish_rate_hz:=30 &
  ODOM_PID=$!
fi

wait_for_topic "${ODOM_TOPIC}"

roslaunch clbrobot "${NAV_LAUNCH}" \
  map_file:="${MAP_FILE}" \
  odom_frame_id:="${ODOM_TOPIC#/}" \
  odom_topic:="${ODOM_TOPIC}" \
  cmd_vel_topic:=/cmd_vel_nav &
NAV_PID=$!

if [ "${START_RVIZ}" = "1" ]; then
  rviz &
  RVIZ_PID=$!
else
  echo "RViz not started automatically. Launch it manually if needed."
fi

if [ -n "${LSM_PID:-}" ]; then
  wait "${LSM_PID}" "${NAV_PID}"
else
  wait "${ODOM_PID}" "${NAV_PID}"
fi
