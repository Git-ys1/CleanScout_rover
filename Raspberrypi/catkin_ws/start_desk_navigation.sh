#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"

source "$ROOT/use_cleanscout_pi.sh"

echo "[start] launching base stack first"
roslaunch "$ROOT/src/clbrobot_project/clbrobot/launch/nav_base_stack.launch" >/tmp/c236_nav_base_foreground.log 2>&1 &
BASE_LAUNCH_PID=$!

echo "[wait] waiting for /scan /odom /csr_base/ack"
for i in $(seq 1 20); do
  have_scan=0
  have_odom=0
  have_ack=0

  rostopic list 2>/dev/null | grep -q '^/scan$' && have_scan=1 || true
  rostopic list 2>/dev/null | grep -q '^/odom$' && have_odom=1 || true
  rostopic list 2>/dev/null | grep -q '^/csr_base/ack$' && have_ack=1 || true

  if [ "$have_scan" -eq 1 ] && [ "$have_odom" -eq 1 ] && [ "$have_ack" -eq 1 ]; then
    break
  fi
  sleep 1
done

echo "[start] launching navigation layer in foreground"
roslaunch "$ROOT/src/clbrobot_project/clbrobot/launch/desk_map_navigation.launch"

kill "$BASE_LAUNCH_PID" 2>/dev/null || true
