cmake_minimum_required(VERSION 3.0.2)
project(clbrobot)

find_package(catkin REQUIRED COMPONENTS
  csrpi_base_bridge
  geometry_msgs
  mpu6050_i2c_bridge
  nav_msgs
  rosbridge_server
  rospy
  sensor_msgs
  std_msgs
  tf2_ros
)

catkin_package()

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

install(DIRECTORY scripts/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/scripts
)
