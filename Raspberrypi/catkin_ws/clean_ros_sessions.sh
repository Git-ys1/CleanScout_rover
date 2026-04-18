#!/usr/bin/env bash
set -euo pipefail

pkill -9 -f roscore || true
pkill -9 -f rosmaster || true
pkill -9 -f roslaunch || true
pkill -9 -f slam_gmapping || true
pkill -9 -f move_base || true
pkill -9 -f rplidarNode || true
pkill -9 -f map_server || true
pkill -9 -f amcl || true
pkill -9 -f clb_base_node || true
pkill -9 -f ekf_localization_node || true
pkill -9 -f wheel_bridge.py || true
pkill -9 -f enc_to_raw_vel.py || true
pkill -9 -f cmdvel_to_wheels.py || true
pkill -9 -f mpu6050_node.py || true
pkill -9 -f apply_calib || true
pkill -9 -f imu_filter_node || true

sleep 2

ps -ef | grep -E 'roscore|rosmaster|roslaunch|slam_gmapping|move_base|map_server|amcl|rplidarNode|clb_base_node|ekf_localization_node|wheel_bridge.py|enc_to_raw_vel.py|cmdvel_to_wheels.py|mpu6050_node.py|apply_calib|imu_filter_node' | grep -v grep || true
