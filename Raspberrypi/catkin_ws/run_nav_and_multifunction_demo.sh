#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
ROSCORE_LOG="/tmp/c331_nav_multi_roscore.log"
RF1_LOG="/tmp/c331_nav_multi_rf1.log"
IMU_LOG="/tmp/c331_nav_multi_imu.log"
LIDAR_LOG="/tmp/c331_nav_multi_lidar.log"
LSM_LOG="/tmp/c331_nav_multi_lsm.log"
NAV_LOG="/tmp/c331_nav_multi_nav.log"
GATE_LOG="/tmp/c331_nav_multi_gate.log"
FAN_LOG="/tmp/c331_nav_multi_fan.log"
EDGE_LOG="/tmp/c331_nav_multi_edge.log"
EDGE_URL="wss://api.hzhhds.top/edge/ros"

get_current_ip() {
  ip route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; ++i) if ($i == "src") { print $(i + 1); exit }}'
}

build_host_from_suffix() {
  local ip="$1"
  local suffix="$2"
  IFS='.' read -r o1 o2 o3 _ <<< "${ip}"
  printf '%s.%s.%s.%s' "${o1}" "${o2}" "${o3}" "${suffix}"
}

CURRENT_IP="$(get_current_ip)"
EDGE_FALLBACK_HOST_SUFFIX="${EDGE_FALLBACK_HOST_SUFFIX:-190}"
EDGE_FALLBACK_HOST="${EDGE_FALLBACK_HOST:-$(build_host_from_suffix "${CURRENT_IP}" "${EDGE_FALLBACK_HOST_SUFFIX}")}"
EDGE_FALLBACK_URL="${EDGE_FALLBACK_URL:-ws://${EDGE_FALLBACK_HOST}:3000/edge/ros}"
EDGE_PRIMARY_FAILURES_BEFORE_FALLBACK="3"
EDGE_DEVICE_ID="csrpi-001"
EDGE_DEVICE_TOKEN="ac27b6d55f9446daae792bccbb51df4438da3c88d7f9d74986276da8898e66d2"
RSP_LOG="/tmp/c331_nav_multi_rsp.log"

source "$ROOT/use_cleanscout_pi.sh"

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
    echo "[nav-multi] ERROR: 后台进程启动后立刻退出，请检查 $log_file"
    return 1
  fi
  printf '%s' "$pid"
}

echo "[nav-multi] clean 旧会话"
bash "$ROOT/clean_mapping_nav_sessions.sh"
bash "$ROOT/clean_edge_relay_sessions.sh" || true

echo "[nav-multi] 启动 roscore"
ROSCORE_PID=$(launch_bg "$ROSCORE_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roscore')

if ! wait_for_master 8; then
  echo "[nav-multi] ERROR: roscore 未在预期时间内就绪"
  exit 1
fi

echo "[nav-multi] 启动 robot_state_publisher"
RSP_PID=$(launch_bg "$RSP_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/robot_state_publisher.launch')

echo "[nav-multi] 启动底盘最小链"
RF1_PID=$(launch_bg "$RF1_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_min.launch')
wait_for_topic /rf1/vel 8 || { echo "[nav-multi] ERROR: /rf1/vel 未就绪"; exit 1; }

echo "[nav-multi] 启动 IMU"
IMU_PID=$(launch_bg "$IMU_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/core/imu_only.launch publish_static_tf:=false')
wait_for_topic /imu/data 8 || { echo "[nav-multi] ERROR: /imu/data 未就绪"; exit 1; }

echo "[nav-multi] 启动雷达"
LIDAR_PID=$(launch_bg "$LIDAR_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/lidar/rplidar.launch publish_static_tf:=false')
wait_for_topic /scan 8 || { echo "[nav-multi] ERROR: /scan 未就绪"; exit 1; }

echo "[nav-multi] 启动 laser_scan_matcher"
LSM_PID=$(launch_bg "$LSM_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/slam/laser_scan_matcher_406.launch')
wait_for_topic /odom_lsm 8 || { echo "[nav-multi] ERROR: /odom_lsm 未就绪"; exit 1; }

echo "[nav-multi] 启动 cmd_vel 安全门控"
GATE_PID=$(launch_bg "$GATE_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/csrpi_base_bridge/launch/cmd_vel_safety_gate.launch input_topic:=/cmd_vel_nav output_topic:=/cmd_vel')

echo "[nav-multi] 启动导航"
NAV_PID=$(launch_bg "$NAV_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/nav/navigation_406_rf1.launch cmd_vel_topic:=/cmd_vel_nav odom_frame_id:=odom_lsm')
wait_for_topic /amcl_pose 8 || { echo "[nav-multi] ERROR: /amcl_pose 未就绪"; exit 1; }
wait_for_topic /move_base/status 8 || { echo "[nav-multi] ERROR: /move_base/status 未就绪"; exit 1; }

echo "[nav-multi] 启动风机多功能桥"
FAN_PID=$(launch_bg "$FAN_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/csrpi_fan_bridge/launch/fan_dual_lid_bridge.launch')

echo "[nav-multi] 启动 edge-relay（允许后端控制风机和手动运动，与导航共存）"
EDGE_PID=$(launch_bg "$EDGE_LOG" "source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/csrpi_edge_relay/launch/edge_relay.launch enabled:=true url:=\"$EDGE_URL\" fallback_url:=\"$EDGE_FALLBACK_URL\" primary_failures_before_fallback:=\"$EDGE_PRIMARY_FAILURES_BEFORE_FALLBACK\" device_id:=\"$EDGE_DEVICE_ID\" device_token:=\"$EDGE_DEVICE_TOKEN\" toggle_motion_enabled:=false allow_manual_control:=true publish_cmd_vel:=true cmd_vel_topic:=/cmd_vel_nav allow_fan_control:=true odom_topic:=/odom_lsm")

echo "[nav-multi] 联合演示链已就绪"
echo "[nav-multi] 导航: 可由 RViz 发 2D Nav Goal"
echo "[nav-multi] 后端: 可经 edge-relay 手动控制运动与风机"
echo "[nav-multi] logs:"
echo "  roscore: $ROSCORE_LOG"
echo "  rsp:     $RSP_LOG"
echo "  rf1:     $RF1_LOG"
echo "  imu:     $IMU_LOG"
echo "  lidar:   $LIDAR_LOG"
echo "  lsm:     $LSM_LOG"
echo "  nav:     $NAV_LOG"
echo "  gate:    $GATE_LOG"
echo "  fan:     $FAN_LOG"
echo "  edge:    $EDGE_LOG"
