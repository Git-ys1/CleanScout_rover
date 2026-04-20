#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
ROSCORE_LOG="/tmp/c331_roscore.log"
RF1_LOG="/tmp/c331_rf1_min.log"
IMU_LOG="/tmp/c331_imu.log"
LIDAR_LOG="/tmp/c331_lidar.log"
LSM_LOG="/tmp/c331_lsm.log"
MAPPING_LOG="/tmp/c331_mapping_406.log"
EDGE_RELAY_LOG="/tmp/c331_edge_relay.log"

ENABLE_EDGE_RELAY="${ENABLE_EDGE_RELAY:-1}"
EDGE_RELAY_URL="${EDGE_RELAY_URL:-ws://10.22.7.190:3000/edge/ros}"
EDGE_DEVICE_ID="${EDGE_DEVICE_ID:-csrpi-001}"
EDGE_DEVICE_TOKEN="${EDGE_DEVICE_TOKEN:-}"
EDGE_HEARTBEAT_MS="${EDGE_HEARTBEAT_MS:-5000}"
EDGE_ODOM_HZ="${EDGE_ODOM_HZ:-5}"
EDGE_IMU_HZ="${EDGE_IMU_HZ:-5}"
EDGE_SCAN_HZ="${EDGE_SCAN_HZ:-1}"
EDGE_CMD_REPEAT_HZ="${EDGE_CMD_REPEAT_HZ:-10}"
EDGE_CMD_DEFAULT_HOLD_MS="${EDGE_CMD_DEFAULT_HOLD_MS:-400}"
EDGE_RECONNECT_DELAY_MS="${EDGE_RECONNECT_DELAY_MS:-1000}"

for arg in "$@"; do
  case "$arg" in
    --without-edge-relay)
      ENABLE_EDGE_RELAY=0
      ;;
    *)
      echo "[c331-mapping] ERROR: 未知参数 $arg"
      echo "[c331-mapping] 用法: bash ./run_slam_mapping.sh [--without-edge-relay]"
      exit 2
      ;;
  esac
done

cleanup_on_error() {
  local code=$?
  if [ "$code" -ne 0 ]; then
    echo "[c331-mapping] ERROR: 启动失败，自动清理残留 ROS 会话"
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
    echo "[c331-mapping] ERROR: 后台进程启动后立刻退出"
    echo "[c331-mapping] ERROR: 请检查日志 $log_file"
    return 1
  fi

  printf '%s' "$pid"
}

start_edge_relay() {
  if [ "$ENABLE_EDGE_RELAY" != "1" ]; then
    return 0
  fi

  if [ -z "$EDGE_DEVICE_TOKEN" ]; then
    echo "[c331-mapping] ERROR: 已请求启动 edge-relay，但 EDGE_DEVICE_TOKEN 为空"
    return 1
  fi

  bash "$ROOT/clean_edge_relay_sessions.sh" || true

  EDGE_RELAY_PID=$(launch_bg "$EDGE_RELAY_LOG" "source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && export ROS_PACKAGE_PATH=\"/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src:/opt/ros/noetic/share\" && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/csrpi_edge_relay/launch/edge_relay.launch enabled:=true url:=\"$EDGE_RELAY_URL\" device_id:=\"$EDGE_DEVICE_ID\" device_token:=\"$EDGE_DEVICE_TOKEN\" heartbeat_ms:=\"$EDGE_HEARTBEAT_MS\" odom_hz:=\"$EDGE_ODOM_HZ\" imu_hz:=\"$EDGE_IMU_HZ\" scan_hz:=\"$EDGE_SCAN_HZ\" cmd_repeat_hz:=\"$EDGE_CMD_REPEAT_HZ\" default_hold_ms:=\"$EDGE_CMD_DEFAULT_HOLD_MS\" reconnect_delay_ms:=\"$EDGE_RECONNECT_DELAY_MS\"")

  echo "[c331-mapping] edge-relay 已启动，日志: $EDGE_RELAY_LOG"
  echo "[c331-mapping] 前端控制链: frontend -> backend -> edge-relay -> /cmd_vel -> RF1"
  echo "[c331-mapping] edge url: $EDGE_RELAY_URL"
}

source "$ROOT/use_cleanscout_pi.sh"

echo "[c331-mapping] clean 旧会话"
bash "$ROOT/clean_mapping_nav_sessions.sh"

echo "[c331-mapping] 显式启动 roscore"
ROSCORE_PID=$(launch_bg "$ROSCORE_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roscore')

if ! wait_for_master 8; then
  echo "[c331-mapping] ERROR: roscore 未在预期时间内就绪"
  echo "[c331-mapping] ERROR: 请检查日志 $ROSCORE_LOG"
  exit 1
fi

echo "[c331-mapping] 启动 bringup_rf1_min.launch (wheel tf 关闭，正式建图默认走 lsm 备线)"
RF1_PID=$(launch_bg "$RF1_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_min.launch publish_odom_tf:=false')

echo "[c331-mapping] 等待 /rf1/vel"
if ! wait_for_topic /rf1/vel 8; then
  echo "[c331-mapping] ERROR: /rf1/vel 未就绪"
  if ! kill -0 "$RF1_PID" 2>/dev/null; then
    echo "[c331-mapping] ERROR: bringup_rf1_min.launch 已退出，请检查 $RF1_LOG"
  fi
  exit 1
fi

echo "[c331-mapping] 启动 imu_only.launch"
IMU_PID=$(launch_bg "$IMU_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/core/imu_only.launch')

echo "[c331-mapping] 等待 /imu/data"
if ! wait_for_topic /imu/data 8; then
  echo "[c331-mapping] ERROR: /imu/data 未就绪"
  if ! kill -0 "$IMU_PID" 2>/dev/null; then
    echo "[c331-mapping] ERROR: imu_only.launch 已退出，请检查 $IMU_LOG"
  fi
  exit 1
fi

echo "[c331-mapping] 启动 lidar/rplidar.launch"
LIDAR_PID=$(launch_bg "$LIDAR_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/lidar/rplidar.launch')

echo "[c331-mapping] 等待 /scan"
if ! wait_for_topic /scan 8; then
  echo "[c331-mapping] ERROR: /scan 未就绪"
  if ! kill -0 "$LIDAR_PID" 2>/dev/null; then
    echo "[c331-mapping] ERROR: lidar/rplidar.launch 已退出，请检查 $LIDAR_LOG"
  fi
  exit 1
fi

if [ "$ENABLE_EDGE_RELAY" = "1" ]; then
  echo "[c331-mapping] 启动 edge-relay 手动控制链"
  start_edge_relay
fi

echo "[c331-mapping] 启动 laser_scan_matcher_406.launch"
LSM_PID=$(launch_bg "$LSM_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/slam/laser_scan_matcher_406.launch')

echo "[c331-mapping] 等待 /odom_lsm"
if ! wait_for_topic /odom_lsm 8; then
  echo "[c331-mapping] ERROR: /odom_lsm 未就绪"
  if ! kill -0 "$LSM_PID" 2>/dev/null; then
    echo "[c331-mapping] ERROR: laser_scan_matcher_406.launch 已退出，请检查 $LSM_LOG"
  fi
  exit 1
fi

echo "[c331-mapping] 启动 slam/mapping_406_rf1.launch"
MAPPING_PID=$(launch_bg "$MAPPING_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/slam/mapping_406_rf1.launch start_lsm:=false')

echo "[c331-mapping] 等待 /map"
if ! wait_for_topic /map 6; then
  echo "[c331-mapping] ERROR: /map 未就绪"
  if ! kill -0 "$MAPPING_PID" 2>/dev/null; then
    echo "[c331-mapping] ERROR: mapping_406_rf1.launch 已退出，请检查 $MAPPING_LOG"
  fi
  exit 1
fi

echo "[c331-mapping] 406 建图链已就绪"
echo "[c331-mapping] 当前正式建图默认走 laser_scan_matcher + gmapping"
echo "[c331-mapping] 现在到上位机 / 虚拟机 RViz 开始建图"
echo "[c331-mapping] 保存地图请运行 save_map.sh"
if [ "$ENABLE_EDGE_RELAY" = "1" ]; then
  echo "[c331-mapping] 当前已启用 edge-relay，可从前端经后端控制小车建图"
fi
trap - EXIT
