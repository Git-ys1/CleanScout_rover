# Install script for directory: /home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_gesture_detect

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
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE FILES "/home/clbrobot/catkin_ws/build/clbrobot_project/clbrobot_gesture_detect/catkin_generated/installspace/clbrobot_gesture_detect.pc")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/clbrobot_gesture_detect/cmake" TYPE FILE FILES
    "/home/clbrobot/catkin_ws/build/clbrobot_project/clbrobot_gesture_detect/catkin_generated/installspace/clbrobot_gesture_detectConfig.cmake"
    "/home/clbrobot/catkin_ws/build/clbrobot_project/clbrobot_gesture_detect/catkin_generated/installspace/clbrobot_gesture_detectConfig-version.cmake"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/clbrobot_gesture_detect" TYPE FILE FILES "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_gesture_detect/package.xml")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/clbrobot_gesture_detect" TYPE PROGRAM FILES
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_gesture_detect/clbrobot_face_detect.py"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_gesture_detect/clbrobot_facehaar_detect.py"
    "/home/clbrobot/catkin_ws/src/clbrobot_project/clbrobot_gesture_detect/clbrobot_ball_detect.py"
    )
endif()

