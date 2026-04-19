#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
LOG_FILE="/tmp/c322_rf1_web_stack.log"

source "$ROOT/use_cleanscout_pi.sh"

if [ -f "/home/clbrobot/catkin_ws/devel/setup.bash" ]; then
  source "/home/clbrobot/catkin_ws/devel/setup.bash"
fi

export ROS_PACKAGE_PATH="$ROOT/src:/home/clbrobot/catkin_ws/src:/opt/ros/noetic/share"

export EDGE_RELAY_ENABLED="${EDGE_RELAY_ENABLED:-false}"
export EDGE_RELAY_URL="${EDGE_RELAY_URL:-wss://api.hzhhds.top/edge/ros}"
export EDGE_DEVICE_ID="${EDGE_DEVICE_ID:-csrpi-001}"
export EDGE_DEVICE_TOKEN="${EDGE_DEVICE_TOKEN:-}"
export EDGE_HEARTBEAT_MS="${EDGE_HEARTBEAT_MS:-5000}"
export EDGE_ODOM_HZ="${EDGE_ODOM_HZ:-5}"
export EDGE_IMU_HZ="${EDGE_IMU_HZ:-5}"
export EDGE_SCAN_HZ="${EDGE_SCAN_HZ:-1}"
export EDGE_CMD_REPEAT_HZ="${EDGE_CMD_REPEAT_HZ:-10}"
export EDGE_CMD_DEFAULT_HOLD_MS="${EDGE_CMD_DEFAULT_HOLD_MS:-400}"
export EDGE_RECONNECT_DELAY_MS="${EDGE_RECONNECT_DELAY_MS:-1000}"

"$ROOT/clean_rf1_web_sessions.sh"

nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && if [ -f "/home/clbrobot/catkin_ws/devel/setup.bash" ]; then source "/home/clbrobot/catkin_ws/devel/setup.bash"; fi && export ROS_PACKAGE_PATH="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src:/home/clbrobot/catkin_ws/src:/opt/ros/noetic/share" && roslaunch "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_web.launch" edge_relay_enabled:="$EDGE_RELAY_ENABLED" edge_relay_url:="$EDGE_RELAY_URL" edge_device_id:="$EDGE_DEVICE_ID" edge_device_token:="$EDGE_DEVICE_TOKEN" edge_heartbeat_ms:="$EDGE_HEARTBEAT_MS" edge_odom_hz:="$EDGE_ODOM_HZ" edge_imu_hz:="$EDGE_IMU_HZ" edge_scan_hz:="$EDGE_SCAN_HZ" edge_cmd_repeat_hz:="$EDGE_CMD_REPEAT_HZ" edge_default_hold_ms:="$EDGE_CMD_DEFAULT_HOLD_MS" edge_reconnect_delay_ms:="$EDGE_RECONNECT_DELAY_MS"' >"$LOG_FILE" 2>&1 </dev/null &

sleep 8

printf '\n[rf1-web] log file\n%s\n' "$LOG_FILE"

printf '\n[rf1-web] rostopic list\n'
rostopic list || true

printf '\n[rf1-web] rosbridge port\n'
ss -ltnp | grep ':9090' || true

printf '\n[rf1-web] stack launched\n'
