cmake_minimum_required(VERSION 3.0.2)
project(csrpi_base_bridge)

find_package(catkin REQUIRED COMPONENTS
  clb_msgs
  geometry_msgs
  nav_msgs
  rospy
  sensor_msgs
  std_msgs
  tf2_ros
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/wheel_bridge.py
  scripts/cmdvel_to_wheels.py
  scripts/enc_to_raw_vel.py
  scripts/rf1_serial_bridge.py
  scripts/cmdvel_to_rf1.py
  scripts/rf1_vel_to_odom.py
  scripts/scan_contract_stub.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
