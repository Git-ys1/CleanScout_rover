# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "clb_msgs: 16 messages, 7 services")

set(MSG_I_FLAGS "-Iclb_msgs:/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg;-Istd_msgs:/opt/ros/noetic/share/std_msgs/cmake/../msg;-Igeometry_msgs:/opt/ros/noetic/share/geometry_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(geneus REQUIRED)
find_package(genlisp REQUIRED)
find_package(gennodejs REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(clb_msgs_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg" "geometry_msgs/Vector3"
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv" ""
)

get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv" NAME_WE)
add_custom_target(_clb_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clb_msgs" "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv" ""
)

#
#  langs = gencpp;geneus;genlisp;gennodejs;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_msg_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)

### Generating Services
_generate_srv_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_srv_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_srv_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_srv_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_srv_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_srv_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)
_generate_srv_cpp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
)

### Generating Module File
_generate_module_cpp(clb_msgs
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(clb_msgs_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(clb_msgs_generate_messages clb_msgs_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_cpp _clb_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clb_msgs_gencpp)
add_dependencies(clb_msgs_gencpp clb_msgs_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clb_msgs_generate_messages_cpp)

### Section generating for lang: geneus
### Generating Messages
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_msg_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)

### Generating Services
_generate_srv_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_srv_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_srv_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_srv_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_srv_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_srv_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)
_generate_srv_eus(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
)

### Generating Module File
_generate_module_eus(clb_msgs
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
  "${ALL_GEN_OUTPUT_FILES_eus}"
)

add_custom_target(clb_msgs_generate_messages_eus
  DEPENDS ${ALL_GEN_OUTPUT_FILES_eus}
)
add_dependencies(clb_msgs_generate_messages clb_msgs_generate_messages_eus)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_eus _clb_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clb_msgs_geneus)
add_dependencies(clb_msgs_geneus clb_msgs_generate_messages_eus)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clb_msgs_generate_messages_eus)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_msg_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)

### Generating Services
_generate_srv_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_srv_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_srv_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_srv_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_srv_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_srv_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)
_generate_srv_lisp(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
)

### Generating Module File
_generate_module_lisp(clb_msgs
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(clb_msgs_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(clb_msgs_generate_messages clb_msgs_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_lisp _clb_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clb_msgs_genlisp)
add_dependencies(clb_msgs_genlisp clb_msgs_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clb_msgs_generate_messages_lisp)

### Section generating for lang: gennodejs
### Generating Messages
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_msg_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)

### Generating Services
_generate_srv_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_srv_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_srv_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_srv_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_srv_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_srv_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)
_generate_srv_nodejs(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
)

### Generating Module File
_generate_module_nodejs(clb_msgs
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
  "${ALL_GEN_OUTPUT_FILES_nodejs}"
)

add_custom_target(clb_msgs_generate_messages_nodejs
  DEPENDS ${ALL_GEN_OUTPUT_FILES_nodejs}
)
add_dependencies(clb_msgs_generate_messages clb_msgs_generate_messages_nodejs)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_nodejs _clb_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clb_msgs_gennodejs)
add_dependencies(clb_msgs_gennodejs clb_msgs_generate_messages_nodejs)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clb_msgs_generate_messages_nodejs)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_msg_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)

### Generating Services
_generate_srv_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_srv_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_srv_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_srv_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_srv_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_srv_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)
_generate_srv_py(clb_msgs
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
)

### Generating Module File
_generate_module_py(clb_msgs
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(clb_msgs_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(clb_msgs_generate_messages clb_msgs_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv" NAME_WE)
add_dependencies(clb_msgs_generate_messages_py _clb_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clb_msgs_genpy)
add_dependencies(clb_msgs_genpy clb_msgs_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clb_msgs_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clb_msgs
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(clb_msgs_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(clb_msgs_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()

if(geneus_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clb_msgs
    DESTINATION ${geneus_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_eus)
  add_dependencies(clb_msgs_generate_messages_eus std_msgs_generate_messages_eus)
endif()
if(TARGET geometry_msgs_generate_messages_eus)
  add_dependencies(clb_msgs_generate_messages_eus geometry_msgs_generate_messages_eus)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clb_msgs
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(clb_msgs_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(clb_msgs_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()

if(gennodejs_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clb_msgs
    DESTINATION ${gennodejs_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_nodejs)
  add_dependencies(clb_msgs_generate_messages_nodejs std_msgs_generate_messages_nodejs)
endif()
if(TARGET geometry_msgs_generate_messages_nodejs)
  add_dependencies(clb_msgs_generate_messages_nodejs geometry_msgs_generate_messages_nodejs)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs)
  install(CODE "execute_process(COMMAND \"/usr/bin/python3\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clb_msgs
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(clb_msgs_generate_messages_py std_msgs_generate_messages_py)
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(clb_msgs_generate_messages_py geometry_msgs_generate_messages_py)
endif()
