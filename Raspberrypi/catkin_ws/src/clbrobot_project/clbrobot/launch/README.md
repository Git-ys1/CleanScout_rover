# clbrobot Launch Index

本页说明 launch 文件的职责和当前状态。日常操作仍优先使用 `catkin_ws/*.sh`，
因为顶层脚本包含网络环境、等待条件、日志和故障清理。

## 当前链路

| 文件 | 职责 | 状态 |
| --- | --- | --- |
| [`nav/navigation_406_rf1_teb.launch`](nav/navigation_406_rf1_teb.launch) | 地图 + AMCL + move_base/TEB | 当前默认导航 |
| [`nav/navigation_406_rf1.launch`](nav/navigation_406_rf1.launch) | 地图 + AMCL + TrajectoryPlannerROS | 当前回退导航 |
| [`amcl.launch`](amcl.launch) | 统一 AMCL 参数 | 当前共享组件 |
| [`bringup_rf1_min.launch`](bringup_rf1_min.launch) | RF1 串口和 Twist 到四轮速度 | 当前硬件组件 |
| [`robot_state_publisher.launch`](robot_state_publisher.launch) | 加载 CleanScout URDF/xacro | 当前几何组件 |
| [`lidar/rplidar.launch`](lidar/rplidar.launch) | RPLIDAR A3 驱动 | 当前雷达组件 |
| [`slam/slam_406_lsm.launch`](slam/slam_406_lsm.launch) | LSM 可选 + gmapping | 当前建图组件 |
| [`slam/laser_scan_matcher_406.launch`](slam/laser_scan_matcher_406.launch) | 纯激光匹配里程计，`use_imu=false` | 旧备线 / 标定 |
| [`slam/mapping_406_rf1.launch`](slam/mapping_406_rf1.launch) | 建图组件薄封装 | 兼容入口 |

## 专项与历史链路

| 文件 | 原用途 | 当前状态 |
| --- | --- | --- |
| [`core/bringup_rf1_core.launch`](core/bringup_rf1_core.launch) | RF1 + RF1 内置 odom | 旧核心链，几何值早于 C-4.1.2 |
| [`bringup_rf1_web.launch`](bringup_rf1_web.launch) | RF1、雷达、rosbridge、edge 一体化 | 旧 Web 联调链，已移除 IMU |
| [`demo/multi_function_demo.launch`](demo/multi_function_demo.launch) | RF1 + 多功能 + edge | 旧联合演示组件 |
| [`bench_full_stack.launch`](bench_full_stack.launch) | UNO 轮桥、EKF、雷达台架 | 旧台架链，已移除 IMU |
| [`core/imu_only.launch`](core/imu_only.launch) | MPU6050 + Madgwick | `C-4.1.7` 已退役，仅历史复现 |
| [`mpu6050_bringup.launch`](mpu6050_bringup.launch) | 包装旧 IMU include | `C-4.1.7` 已退役，仅历史复现 |
| [`include/imu/imu.launch`](include/imu/imu.launch) | IMU 子链 | `C-4.1.7` 已退役，仅历史复现 |
| [`include/imu/mpu6050_chain.launch`](include/imu/mpu6050_chain.launch) | 旧 MPU6050 滤波链 | `C-4.1.7` 已退役，仅历史复现 |
| [`desk_map_navigation.launch`](desk_map_navigation.launch) | 桌面地图 + 旧 wheel bridge | 历史兼容 |
| [`nav/nav_406.launch`](nav/nav_406.launch) | 最简 map/amcl/move_base | 参数不完整，不作实车默认 |
| [`nav_base_stack.launch`](nav_base_stack.launch) | 旧台架底盘 + 静态雷达 TF | 历史兼容 |
| [`slam/slam_406.launch`](slam/slam_406.launch) | 最简 gmapping | 历史兼容 |
| [`slam/lidar_slam_pi.launch`](slam/lidar_slam_pi.launch) | 旧 Pi SLAM 包装 | 待退役，引用的 `lidar_slam.launch` 已不存在 |

## 维护检查

| 检查项 | 要求 |
| --- | --- |
| XML | `xmllint --noout` 或 `roslaunch-check` 通过 |
| include | 被引用文件必须存在，参数名保持一致 |
| TF | 不重复发布 `map -> odom`、`odom -> base_link` 和传感器静态 TF |
| odom | 确认 frame、topic 和 `publish_tf` 与运行模式一致 |
| cmd_vel | 导航输出应指向 `/cmd_vel_nav` 或由顶层入口明确覆盖 |
| 中文注释 | 仅写入注释，发布前在 `LC_ALL=C` 下复查解析 |
