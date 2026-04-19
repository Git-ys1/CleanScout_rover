#!/usr/bin/env bash
set -euo pipefail

pkill -9 -f roscore || true
pkill -9 -f rosmaster || true
pkill -9 -f roslaunch || true
pkill -9 -f rf1_serial_bridge.py || true
pkill -9 -f cmdvel_to_rf1.py || true
pkill -9 -f rf1_vel_to_odom.py || true
pkill -9 -f mpu6050_node.py || true
pkill -9 -f rplidarNode || true
pkill -9 -f slam_gmapping || true
pkill -9 -f map_server || true
pkill -9 -f amcl || true
pkill -9 -f move_base || true
pkill -9 -f rviz || true

sleep 2

ps -ef | grep -E 'roscore|rosmaster|roslaunch|rf1_serial_bridge.py|cmdvel_to_rf1.py|rf1_vel_to_odom.py|mpu6050_node.py|rplidarNode|slam_gmapping|map_server|amcl|move_base|rviz' | grep -v grep || true
