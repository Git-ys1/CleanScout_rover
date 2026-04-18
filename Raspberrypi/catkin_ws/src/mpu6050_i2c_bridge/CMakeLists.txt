cmake_minimum_required(VERSION 3.0.2)
project(mpu6050_i2c_bridge)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  rospy
  sensor_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/mpu6050_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
