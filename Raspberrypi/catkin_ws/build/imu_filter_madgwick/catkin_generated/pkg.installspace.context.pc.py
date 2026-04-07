# generated from catkin/cmake/template/pkg.context.pc.in
CATKIN_PACKAGE_PREFIX = ""
PROJECT_PKG_CONFIG_INCLUDE_DIRS = "${prefix}/include;/usr/include/boost".split(';') if "${prefix}/include;/usr/include/boost" != "" else []
PROJECT_CATKIN_DEPENDS = "roscpp;sensor_msgs;geometry_msgs;tf2_ros;tf2_geometry_msgs;nodelet;pluginlib;message_filters;dynamic_reconfigure".replace(';', ' ')
PKG_CONFIG_LIBRARIES_WITH_PREFIX = "-limu_filter;-limu_filter_nodelet".split(';') if "-limu_filter;-limu_filter_nodelet" != "" else []
PROJECT_NAME = "imu_filter_madgwick"
PROJECT_SPACE_DIR = "/home/clbrobot/catkin_ws/install"
PROJECT_VERSION = "1.1.6"
