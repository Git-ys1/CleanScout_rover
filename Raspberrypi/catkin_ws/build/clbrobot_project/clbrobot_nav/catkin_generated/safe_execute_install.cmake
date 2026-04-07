execute_process(COMMAND "/home/clbrobot/catkin_ws/build/clbrobot_project/clbrobot_nav/catkin_generated/python_distutils_install.sh" RESULT_VARIABLE res)

if(NOT res EQUAL 0)
  message(FATAL_ERROR "execute_process(/home/clbrobot/catkin_ws/build/clbrobot_project/clbrobot_nav/catkin_generated/python_distutils_install.sh) returned error code ")
endif()
