cmake_minimum_required(VERSION 3.0.2)
project(mpu6050_i2c_bridge)

find_package(catkin REQUIRED COMPONENTS
  clb_msgs
  geometry_msgs
  rospy
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/mpu6050_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
