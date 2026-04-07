# Install script for directory: /home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/clbrobot/catkin_ws/install")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/clb_msgs/msg" TYPE FILE FILES
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Velocities.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/PID.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Imu.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Battery.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/DHT22.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Servo.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Infrared.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Ultrasonic.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Led.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Buzzer.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Arm.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Sonar.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/RcMode.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Bluetooth.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/Blue_connect.msg"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/msg/ps2_value.msg"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/clb_msgs/srv" TYPE FILE FILES
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/ServoAngle.srv"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/RobotVoiceCtrl.srv"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/FaceVoiceSet.srv"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Pose.srv"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Gripper.srv"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Trajectory.srv"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/srv/Shoot.srv"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/clb_msgs/cmake" TYPE FILE FILES "/home/clbrobot/catkin_ws/build/clbrobot_project/clb_msgs/catkin_generated/installspace/clb_msgs-msg-paths.cmake")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include" TYPE DIRECTORY FILES "/home/clbrobot/catkin_ws/devel/include/clb_msgs")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/roseus/ros" TYPE DIRECTORY FILES "/home/clbrobot/catkin_ws/devel/share/roseus/ros/clb_msgs")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/common-lisp/ros" TYPE DIRECTORY FILES "/home/clbrobot/catkin_ws/devel/share/common-lisp/ros/clb_msgs")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/gennodejs/ros" TYPE DIRECTORY FILES "/home/clbrobot/catkin_ws/devel/share/gennodejs/ros/clb_msgs")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  execute_process(COMMAND "/usr/bin/python3" -m compileall "/home/clbrobot/catkin_ws/devel/lib/python3/dist-packages/clb_msgs")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/dist-packages" TYPE DIRECTORY FILES "/home/clbrobot/catkin_ws/devel/lib/python3/dist-packages/clb_msgs")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE FILES "/home/clbrobot/catkin_ws/build/clbrobot_project/clb_msgs/catkin_generated/installspace/clb_msgs.pc")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/clb_msgs/cmake" TYPE FILE FILES "/home/clbrobot/catkin_ws/build/clbrobot_project/clb_msgs/catkin_generated/installspace/clb_msgs-msg-extras.cmake")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/clb_msgs/cmake" TYPE FILE FILES
    "/home/clbrobot/catkin_ws/build/clbrobot_project/clb_msgs/catkin_generated/installspace/clb_msgsConfig.cmake"
    "/home/clbrobot/catkin_ws/build/clbrobot_project/clb_msgs/catkin_generated/installspace/clb_msgsConfig-version.cmake"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/clb_msgs" TYPE FILE FILES "/home/clbrobot/catkin_ws/src/clbrobot_project/clb_msgs/package.xml")
endif()

