#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
ROSCORE_LOG="/tmp/c331_remote_only_roscore.log"
RF1_LOG="/tmp/c331_remote_only_rf1.log"
EDGE_LOG="/tmp/c331_remote_only_edge.log"

source "$ROOT/use_cleanscout_pi.sh"

export EDGE_RELAY_URL="${EDGE_RELAY_URL:-ws://10.22.7.190:3000/edge/ros}"
export EDGE_DEVICE_ID="${EDGE_DEVICE_ID:-csrpi-001}"
export EDGE_DEVICE_TOKEN="${EDGE_DEVICE_TOKEN:-}"
export EDGE_HEARTBEAT_MS="${EDGE_HEARTBEAT_MS:-5000}"
export EDGE_ODOM_HZ="${EDGE_ODOM_HZ:-0}"
export EDGE_IMU_HZ="${EDGE_IMU_HZ:-0}"
export EDGE_SCAN_HZ="${EDGE_SCAN_HZ:-0}"
export EDGE_CMD_REPEAT_HZ="${EDGE_CMD_REPEAT_HZ:-10}"
export EDGE_CMD_DEFAULT_HOLD_MS="${EDGE_CMD_DEFAULT_HOLD_MS:-400}"
export EDGE_RECONNECT_DELAY_MS="${EDGE_RECONNECT_DELAY_MS:-1000}"

wait_for_master() {
  local timeout_sec="$1"
  local step="0.2"
  local elapsed="0"
  while (( $(awk "BEGIN {print ($elapsed < $timeout_sec)}") )); do
    if rosparam get /rosdistro >/dev/null 2>&1; then
      return 0
    fi
    sleep "$step"
    elapsed=$(awk "BEGIN {print $elapsed + $step}")
  done
  return 1
}

wait_for_topic() {
  local topic="$1"
  local timeout_sec="$2"
  local step="0.2"
  local elapsed="0"
  while (( $(awk "BEGIN {print ($elapsed < $timeout_sec)}") )); do
    if rostopic list 2>/dev/null | grep -qx "$topic"; then
      return 0
    fi
    sleep "$step"
    elapsed=$(awk "BEGIN {print $elapsed + $step}")
  done
  return 1
}

launch_bg() {
  local log_file="$1"
  shift
  nohup bash -lc "$*" >"$log_file" 2>&1 </dev/null &
  local pid=$!
  sleep 1
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[remote-only] ERROR: 后台进程启动后立刻退出，请检查 $log_file"
    return 1
  fi
  printf '%s' "$pid"
}

echo "[remote-only] clean 旧会话"
bash "$ROOT/clean_mapping_nav_sessions.sh"
bash "$ROOT/clean_edge_relay_sessions.sh" || true

if [ -z "$EDGE_DEVICE_TOKEN" ]; then
  echo "[remote-only] ERROR: EDGE_DEVICE_TOKEN 为空"
  exit 1
fi

echo "[remote-only] 启动 roscore"
ROSCORE_PID=$(launch_bg "$ROSCORE_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roscore')

if ! wait_for_master 8; then
  echo "[remote-only] ERROR: roscore 未在预期时间内就绪"
  exit 1
fi

echo "[remote-only] 启动最小 RF1 遥控链"
RF1_PID=$(launch_bg "$RF1_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_min.launch')

if ! wait_for_topic /rf1/vel 8; then
  echo "[remote-only] ERROR: /rf1/vel 未就绪，请检查 $RF1_LOG"
  exit 1
fi

echo "[remote-only] 启动 edge-relay"
EDGE_PID=$(launch_bg "$EDGE_LOG" "source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/csrpi_edge_relay/launch/edge_relay.launch enabled:=true url:=\"$EDGE_RELAY_URL\" device_id:=\"$EDGE_DEVICE_ID\" device_token:=\"$EDGE_DEVICE_TOKEN\" heartbeat_ms:=\"$EDGE_HEARTBEAT_MS\" odom_hz:=\"$EDGE_ODOM_HZ\" imu_hz:=\"$EDGE_IMU_HZ\" scan_hz:=\"$EDGE_SCAN_HZ\" cmd_repeat_hz:=\"$EDGE_CMD_REPEAT_HZ\" default_hold_ms:=\"$EDGE_CMD_DEFAULT_HOLD_MS\" reconnect_delay_ms:=\"$EDGE_RECONNECT_DELAY_MS\"")

echo "[remote-only] 遥控链已就绪"
echo "[remote-only] frontend -> backend -> edge-relay -> /cmd_vel -> RF1"
echo "[remote-only] edge url: $EDGE_RELAY_URL"
echo "[remote-only] roscore log: $ROSCORE_LOG"
echo "[remote-only] rf1 log: $RF1_LOG"
echo "[remote-only] edge log: $EDGE_LOG"
