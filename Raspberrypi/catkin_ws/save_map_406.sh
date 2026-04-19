#!/usr/bin/env bash
set -euo pipefail

source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh"

echo "[c330-save] 保存 406 地图到 clbrobot/maps/406"
rosrun map_server map_saver -f "$(rospack find clbrobot)/maps/406"

echo "[c330-save] 期望输出：406.yaml / 406.pgm"
