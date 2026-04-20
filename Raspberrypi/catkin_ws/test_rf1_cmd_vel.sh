#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
ROSCORE_LOG="/tmp/c331_rf1_test_roscore.log"
RF1_LOG="/tmp/c331_rf1_test_bridge.log"

cleanup_on_error() {
  local code=$?
  if [ "$code" -ne 0 ]; then
    echo "[rf1-test] ERROR: 自检失败，自动清理最小 RF1 会话"
    bash "$ROOT/clean_mapping_nav_sessions.sh" || true
  fi
  exit "$code"
}

trap cleanup_on_error EXIT

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

launch_bg() {
  local log_file="$1"
  shift

  nohup bash -lc "$*" >"$log_file" 2>&1 </dev/null &
  local pid=$!
  sleep 1
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[rf1-test] ERROR: 后台进程启动后立刻退出，请检查 $log_file"
    return 1
  fi
  printf '%s' "$pid"
}

send_cmd_pulse() {
  local name="$1"
  local x="$2"
  local y="$3"
  local z="$4"

  echo "[rf1-test] 持续发送 $name 2 秒: vx=$x vy=$y wz=$z"
  timeout 2s rostopic pub -r 10 /cmd_vel geometry_msgs/Twist "{linear: {x: $x, y: $y, z: 0.0}, angular: {x: 0.0, y: 0.0, z: $z}}" >/dev/null 2>&1 || true
  sleep 0.5

  echo "[rf1-test] /rf1/wheel_target_ms 快照 ($name)"
  rostopic echo -n 3 /rf1/wheel_target_ms || true

  echo "[rf1-test] /rf1/cmdvel_debug 快照 ($name)"
  rostopic echo -n 3 /rf1/cmdvel_debug || true

  echo "[rf1-test] /rf1/status 快照 ($name)"
  rostopic echo -n 3 /rf1/status || true
}

source "$ROOT/use_cleanscout_pi.sh"

echo "[rf1-test] clean 旧会话"
bash "$ROOT/clean_mapping_nav_sessions.sh"

echo "[rf1-test] 启动 roscore"
ROSCORE_PID=$(launch_bg "$ROSCORE_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roscore')

if ! wait_for_master 8; then
  echo "[rf1-test] ERROR: roscore 未在预期时间内就绪"
  echo "[rf1-test] ERROR: 请检查日志 $ROSCORE_LOG"
  exit 1
fi

echo "[rf1-test] 启动最小 RF1 主动控制链"
RF1_PID=$(launch_bg "$RF1_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_min.launch')

echo "[rf1-test] 等待 /rf1/vel"
if ! wait_for_topic /rf1/vel 10; then
  echo "[rf1-test] ERROR: /rf1/vel 未就绪，请检查 $RF1_LOG"
  exit 1
fi

echo "[rf1-test] 等待 /rf1/wheel_target_ms"
if ! wait_for_topic /rf1/wheel_target_ms 5; then
  echo "[rf1-test] ERROR: /rf1/wheel_target_ms 未就绪，请检查 $RF1_LOG"
  exit 1
fi

echo "[rf1-test] 当前 topic 检查"
rostopic list | grep -E '^/cmd_vel$|^/rf1/vel$|^/rf1/wheel_target_ms$|^/rf1/status$|^/rf1/cmdvel_debug$' || true

send_cmd_pulse "forward" "0.08" "0.0" "0.0"
sleep 1
send_cmd_pulse "backward" "-0.08" "0.0" "0.0"
sleep 1
send_cmd_pulse "left-strafe" "0.0" "0.06" "0.0"
sleep 1
send_cmd_pulse "rotate" "0.0" "0.0" "0.25"

echo "[rf1-test] 自检结束，已自动发送多组 2 秒持续控制"
echo "[rf1-test] 请观察小车是否有明显前进/后退/横移/旋转动作"
echo "[rf1-test] 桥接日志: $RF1_LOG"
echo "[rf1-test] roscore 日志: $ROSCORE_LOG"
echo "[rf1-test] 如需结束，请执行: bash ./clean_mapping_nav_sessions.sh"
trap - EXIT
