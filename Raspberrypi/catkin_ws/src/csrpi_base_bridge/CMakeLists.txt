cmake_minimum_required(VERSION 3.0.2)
project(csrpi_base_bridge)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  rospy
  std_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/wheel_bridge.py
  scripts/cmdvel_to_wheels.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
