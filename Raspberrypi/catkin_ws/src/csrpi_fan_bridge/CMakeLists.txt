cmake_minimum_required(VERSION 3.0.2)
project(csrpi_fan_bridge)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/fan_pwm_test.py
  scripts/fan_bridge.py
  scripts/relay_toggle_test.py
  scripts/fan_dual_test.py
  scripts/fan_dual_bridge.py
  scripts/fan_dual_fg_test.py
  scripts/servo_gpio12_test.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
