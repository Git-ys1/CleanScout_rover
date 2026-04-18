# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "clbrobot_lidar_follower: 1 messages, 0 services")

set(MSG_I_FLAGS "-Iclbrobot_lidar_follower:/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg;-Istd_msgs:/opt/ros/noetic/share/std_msgs/cmake/../msg;-Isensor_msgs:/opt/ros/noetic/share/sensor_msgs/cmake/../msg;-Igeometry_msgs:/opt/ros/noetic/share/geometry_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(geneus REQUIRED)
find_package(genlisp REQUIRED)
find_package(gennodejs REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(clbrobot_lidar_follower_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg" NAME_WE)
add_custom_target(_clbrobot_lidar_follower_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "clbrobot_lidar_follower" "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg" ""
)

#
#  langs = gencpp;geneus;genlisp;gennodejs;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(clbrobot_lidar_follower
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clbrobot_lidar_follower
)

### Generating Services

### Generating Module File
_generate_module_cpp(clbrobot_lidar_follower
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clbrobot_lidar_follower
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(clbrobot_lidar_follower_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(clbrobot_lidar_follower_generate_messages clbrobot_lidar_follower_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg" NAME_WE)
add_dependencies(clbrobot_lidar_follower_generate_messages_cpp _clbrobot_lidar_follower_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clbrobot_lidar_follower_gencpp)
add_dependencies(clbrobot_lidar_follower_gencpp clbrobot_lidar_follower_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clbrobot_lidar_follower_generate_messages_cpp)

### Section generating for lang: geneus
### Generating Messages
_generate_msg_eus(clbrobot_lidar_follower
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clbrobot_lidar_follower
)

### Generating Services

### Generating Module File
_generate_module_eus(clbrobot_lidar_follower
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clbrobot_lidar_follower
  "${ALL_GEN_OUTPUT_FILES_eus}"
)

add_custom_target(clbrobot_lidar_follower_generate_messages_eus
  DEPENDS ${ALL_GEN_OUTPUT_FILES_eus}
)
add_dependencies(clbrobot_lidar_follower_generate_messages clbrobot_lidar_follower_generate_messages_eus)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg" NAME_WE)
add_dependencies(clbrobot_lidar_follower_generate_messages_eus _clbrobot_lidar_follower_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clbrobot_lidar_follower_geneus)
add_dependencies(clbrobot_lidar_follower_geneus clbrobot_lidar_follower_generate_messages_eus)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clbrobot_lidar_follower_generate_messages_eus)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(clbrobot_lidar_follower
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clbrobot_lidar_follower
)

### Generating Services

### Generating Module File
_generate_module_lisp(clbrobot_lidar_follower
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clbrobot_lidar_follower
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(clbrobot_lidar_follower_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(clbrobot_lidar_follower_generate_messages clbrobot_lidar_follower_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg" NAME_WE)
add_dependencies(clbrobot_lidar_follower_generate_messages_lisp _clbrobot_lidar_follower_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clbrobot_lidar_follower_genlisp)
add_dependencies(clbrobot_lidar_follower_genlisp clbrobot_lidar_follower_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clbrobot_lidar_follower_generate_messages_lisp)

### Section generating for lang: gennodejs
### Generating Messages
_generate_msg_nodejs(clbrobot_lidar_follower
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clbrobot_lidar_follower
)

### Generating Services

### Generating Module File
_generate_module_nodejs(clbrobot_lidar_follower
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clbrobot_lidar_follower
  "${ALL_GEN_OUTPUT_FILES_nodejs}"
)

add_custom_target(clbrobot_lidar_follower_generate_messages_nodejs
  DEPENDS ${ALL_GEN_OUTPUT_FILES_nodejs}
)
add_dependencies(clbrobot_lidar_follower_generate_messages clbrobot_lidar_follower_generate_messages_nodejs)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg" NAME_WE)
add_dependencies(clbrobot_lidar_follower_generate_messages_nodejs _clbrobot_lidar_follower_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clbrobot_lidar_follower_gennodejs)
add_dependencies(clbrobot_lidar_follower_gennodejs clbrobot_lidar_follower_generate_messages_nodejs)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clbrobot_lidar_follower_generate_messages_nodejs)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(clbrobot_lidar_follower
  "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clbrobot_lidar_follower
)

### Generating Services

### Generating Module File
_generate_module_py(clbrobot_lidar_follower
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clbrobot_lidar_follower
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(clbrobot_lidar_follower_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(clbrobot_lidar_follower_generate_messages clbrobot_lidar_follower_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_lidar_follower/msg/position.msg" NAME_WE)
add_dependencies(clbrobot_lidar_follower_generate_messages_py _clbrobot_lidar_follower_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(clbrobot_lidar_follower_genpy)
add_dependencies(clbrobot_lidar_follower_genpy clbrobot_lidar_follower_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS clbrobot_lidar_follower_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clbrobot_lidar_follower)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/clbrobot_lidar_follower
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(clbrobot_lidar_follower_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()
if(TARGET sensor_msgs_generate_messages_cpp)
  add_dependencies(clbrobot_lidar_follower_generate_messages_cpp sensor_msgs_generate_messages_cpp)
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(clbrobot_lidar_follower_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()

if(geneus_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clbrobot_lidar_follower)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/clbrobot_lidar_follower
    DESTINATION ${geneus_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_eus)
  add_dependencies(clbrobot_lidar_follower_generate_messages_eus std_msgs_generate_messages_eus)
endif()
if(TARGET sensor_msgs_generate_messages_eus)
  add_dependencies(clbrobot_lidar_follower_generate_messages_eus sensor_msgs_generate_messages_eus)
endif()
if(TARGET geometry_msgs_generate_messages_eus)
  add_dependencies(clbrobot_lidar_follower_generate_messages_eus geometry_msgs_generate_messages_eus)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clbrobot_lidar_follower)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/clbrobot_lidar_follower
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(clbrobot_lidar_follower_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()
if(TARGET sensor_msgs_generate_messages_lisp)
  add_dependencies(clbrobot_lidar_follower_generate_messages_lisp sensor_msgs_generate_messages_lisp)
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(clbrobot_lidar_follower_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()

if(gennodejs_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clbrobot_lidar_follower)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/clbrobot_lidar_follower
    DESTINATION ${gennodejs_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_nodejs)
  add_dependencies(clbrobot_lidar_follower_generate_messages_nodejs std_msgs_generate_messages_nodejs)
endif()
if(TARGET sensor_msgs_generate_messages_nodejs)
  add_dependencies(clbrobot_lidar_follower_generate_messages_nodejs sensor_msgs_generate_messages_nodejs)
endif()
if(TARGET geometry_msgs_generate_messages_nodejs)
  add_dependencies(clbrobot_lidar_follower_generate_messages_nodejs geometry_msgs_generate_messages_nodejs)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clbrobot_lidar_follower)
  install(CODE "execute_process(COMMAND \"/usr/bin/python3\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clbrobot_lidar_follower\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/clbrobot_lidar_follower
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(clbrobot_lidar_follower_generate_messages_py std_msgs_generate_messages_py)
endif()
if(TARGET sensor_msgs_generate_messages_py)
  add_dependencies(clbrobot_lidar_follower_generate_messages_py sensor_msgs_generate_messages_py)
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(clbrobot_lidar_follower_generate_messages_py geometry_msgs_generate_messages_py)
endif()
