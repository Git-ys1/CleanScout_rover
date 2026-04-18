#!/usr/bin/env bash
set -euo pipefail

IP="$(hostname -I | awk '{print $1}')"

echo "[check] current shell env"
env | grep -E '^ROS_MASTER_URI=|^ROS_IP=|^ROS_HOSTNAME=' || true

echo
echo "[check] roscore/rosmaster/roslaunch processes"
ps -ef | grep -E 'roscore|rosmaster|roslaunch' | grep -v grep || true

echo
echo "[check] port 11311"
python3 - <<PY
import socket
for host in ('127.0.0.1', '$IP'):
    s = socket.socket()
    try:
        s.settimeout(1.0)
        s.connect((host, 11311))
        print(host, 'open')
    except Exception as e:
        print(host, 'closed', e)
    finally:
        s.close()
PY

echo
echo "[check] ROS topics"
source /opt/ros/noetic/setup.bash
rostopic list 2>/dev/null || true

echo
echo "[check] key topics"
for topic in /scan /odom /csr_base/ack /amcl_pose /move_base/status /cmd_vel /csr_base/wheel_targets; do
  if rostopic list 2>/dev/null | grep -q "^${topic}$"; then
    echo "ok  ${topic}"
  else
    echo "miss ${topic}"
  fi
done
