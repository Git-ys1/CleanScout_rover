# CleanScout ROS Packages

本目录混合存放 CleanScout 自研包和固定版本的第三方 ROS Noetic 源码。
不要仅凭目录名删除包；先检查 `package.xml`、launch 引用和运行入口。

## 自研包

| 包 | 版本 | 职责 | 维护级别 |
| --- | --- | --- | --- |
| [`clbrobot`](clbrobot_project/clbrobot/) | `0.0.1` | 整车 launch、导航参数、地图、URDF | 核心 |
| [`cleanscout_navigation`](cleanscout_navigation/) | `0.1.0` | 路线记录、执行与导航任务 | 业务功能 |
| [`csrpi_base_bridge`](csrpi_base_bridge/) | `0.0.1` | RF1 串口、轮速、里程计、速度安全门 | 核心 |
| [`csrpi_edge_relay`](csrpi_edge_relay/) | `0.0.1` | ROS 与后端 WebSocket 中继 | 核心 |
| [`csrpi_fan_bridge`](csrpi_fan_bridge/) | `0.0.1` | 风机、继电器、顶盖执行器桥接 | 核心 |
| [`csrpi_openmv_bridge`](csrpi_openmv_bridge/) | `0.1.0` | OpenMV 串口数据桥接 | 可选感知 |
| [`mpu6050_i2c_bridge`](mpu6050_i2c_bridge/) | `0.0.1` | MPU6050 I2C 原始 IMU 发布 | 核心传感器 |

## 传感器与感知依赖

| 目录 / 包 | 版本 | 用途 | 来源性质 |
| --- | --- | --- | --- |
| [`rplidar_ros`](rplidar_ros/) | `1.10.0` | RPLIDAR A3 `/scan` 驱动 | vendored |
| [`depth_camera`](depth_camera/) | Astra `0.3.0/0.2.2` | Astra 深度相机驱动与启动 | vendored |
| [`depthimage_to_laserscan`](depth_camera/depthimage_to_laserscan/) | `1.0.8` | 深度图转 LaserScan | vendored |
| [`imu_tools`](imu_tools/) | `1.2.7` | Madgwick/互补滤波、RViz IMU | vendored |
| [`opencv_apps`](opencv_apps/) | `2.0.2` | OpenCV ROS 节点集合 | vendored |

## 导航与 SLAM 依赖

| 目录 / 包 | 版本 | 用途 | 当前关系 |
| --- | --- | --- | --- |
| [`teb_local_planner-noetic-devel`](teb_local_planner-noetic-devel/) | `0.9.1` | TEB 局部规划器 | 当前默认 |
| [`costmap_converter-master`](costmap_converter-master/) | `0.0.13` | TEB 障碍物转换依赖 | TEB 依赖 |
| [`laser_scan_matcher-master`](laser_scan_matcher-master/) | `0.3.2` | 激光匹配里程计 | 可选 / 标定 |
| [`move_base_flex`](move_base_flex/) | `0.4.0` | MBF 框架及 8 个子包 | vendored，非当前默认入口 |

TEB 固定依赖说明见 [`TEB_DEPENDENCY_LOCK.md`](TEB_DEPENDENCY_LOCK.md)。

## 目录治理

| 规则 | 说明 |
| --- | --- |
| 自研修改 | 应集中在自研包，避免直接改第三方源码 |
| 第三方升级 | 记录来源、版本、补丁和回归结果 |
| 嵌套 Git | vendored 目录不得保留内部 `.git/` |
| 包级说明 | 自研核心包应提供标准 `README.md` |
| 删除判断 | 同时检查 `rospack depends`、launch、shell 和文档引用 |
| 构建验证 | 至少运行目标包 catkin 构建；共享导航依赖需扩大验证范围 |

## 快速定位

| 要改的内容 | 首选位置 |
| --- | --- |
| 导航、AMCL、costmap、TEB | `clbrobot_project/clbrobot/param/navigation/` |
| 整车启动编排 | `clbrobot_project/clbrobot/launch/` |
| RF1、odom、安全门 | `csrpi_base_bridge/` |
| 雷达 | `rplidar_ros/` 与 `clbrobot/.../launch/lidar/` |
| IMU | `mpu6050_i2c_bridge/`、`imu_tools/` 与 `clbrobot/.../launch/core/` |
| 深度相机 | `depth_camera/` |
| 后端远控 | `csrpi_edge_relay/` |
| 风机与顶盖 | `csrpi_fan_bridge/` |
