#!/usr/bin/env bash
set -euo pipefail

pkill -9 -f roscore || true
pkill -9 -f rosmaster || true
pkill -9 -f roslaunch || true
pkill -9 -f rosbridge_websocket || true
pkill -9 -f rf1_serial_bridge.py || true
pkill -9 -f cmdvel_to_rf1.py || true
pkill -9 -f rf1_vel_to_odom.py || true
pkill -9 -f scan_contract_stub.py || true
pkill -9 -f mpu6050_node.py || true
pkill -9 -f rplidarNode || true

sleep 2

ps -ef | grep -E 'roscore|rosmaster|roslaunch|rosbridge_websocket|rf1_serial_bridge.py|cmdvel_to_rf1.py|rf1_vel_to_odom.py|scan_contract_stub.py|mpu6050_node.py|rplidarNode' | grep -v grep || true
