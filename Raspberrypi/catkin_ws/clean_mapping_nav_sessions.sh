#!/usr/bin/env bash
set -euo pipefail

for pattern in \
  roscore \
  rosmaster \
  roslaunch \
  rf1_serial_bridge.py \
  cmdvel_to_rf1.py \
  rf1_vel_to_odom.py \
  mpu6050_node.py \
  rplidarNode \
  slam_gmapping \
  map_server \
  amcl \
  move_base; do
  pkill -f "$pattern" || true
done

sleep 1

for pattern in \
  roscore \
  rosmaster \
  roslaunch \
  rf1_serial_bridge.py \
  cmdvel_to_rf1.py \
  rf1_vel_to_odom.py \
  mpu6050_node.py \
  rplidarNode \
  slam_gmapping \
  map_server \
  amcl \
  move_base; do
  pkill -9 -f "$pattern" || true
done

sleep 1

ps -ef | grep -E 'roscore|rosmaster|roslaunch|rf1_serial_bridge.py|cmdvel_to_rf1.py|rf1_vel_to_odom.py|mpu6050_node.py|rplidarNode|slam_gmapping|map_server|amcl|move_base' | grep -v grep || true
