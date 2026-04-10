#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"

pkill -9 -f roscore || true
pkill -9 -f rosmaster || true
pkill -9 -f roslaunch || true
pkill -9 -f rplidarNode || true
pkill -9 -f mpu6050_node.py || true
pkill -9 -f apply_calib || true
pkill -9 -f imu_filter_node || true
pkill -9 -f wheel_bridge.py || true
pkill -9 -f slam_gmapping || true
pkill -9 -f move_base || true

export ROS_MASTER_URI="http://127.0.0.1:11311"
export ROS_IP="127.0.0.1"
export ROS_HOSTNAME="127.0.0.1"
export CLBLIDAR="rplidar"
export CLBBASE="mecanum"

source /opt/ros/noetic/setup.bash
source "$ROOT/devel/setup.bash"

nohup bash -lc 'export ROS_MASTER_URI=http://127.0.0.1:11311 ROS_IP=127.0.0.1 ROS_HOSTNAME=127.0.0.1; source /opt/ros/noetic/setup.bash; /usr/bin/python3 /opt/ros/noetic/bin/rosmaster --core -p 11311 -w 3' >/tmp/c233_master.log 2>&1 </dev/null &
sleep 2

nohup bash -lc 'export ROS_MASTER_URI=http://127.0.0.1:11311 ROS_IP=127.0.0.1 ROS_HOSTNAME=127.0.0.1 CLBLIDAR=rplidar CLBBASE=mecanum; source /opt/ros/noetic/setup.bash; source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/devel/setup.bash; roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/slam/lidar_slam_pi.launch' >/tmp/c233_slam.log 2>&1 </dev/null &

sleep 10

printf '\n[c233] rostopic list\n'
rostopic list || true

printf '\n[c233] rostopic hz /scan\n'
timeout 8 rostopic hz /scan || true

printf '\n[c233] rostopic hz /imu/data\n'
timeout 8 rostopic hz /imu/data || true

printf '\n[c233] rostopic echo -n 1 /odom\n'
timeout 8 rostopic echo -n 1 /odom || true

printf '\n[c233] tf check reminder: inspect odom->base_footprint/base_link, base_footprint->imu_link, base_link->laser in RViz\n'
