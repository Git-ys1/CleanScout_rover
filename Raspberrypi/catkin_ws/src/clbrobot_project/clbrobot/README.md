# clbrobot

`clbrobot` 是 CleanScout 的整车配置包。它不承载大部分硬件驱动，而负责把底盘、
传感器、TF、地图、定位、规划和可视化装配成可运行链路。

## 目录

| 路径 | 内容 | 说明 |
| --- | --- | --- |
| [`launch/`](launch/) | 整车与子系统 launch | 先看状态表再直接运行 |
| [`param/`](param/) | 导航、EKF 等参数 | 导航说明见 [`param/navigation/README.md`](param/navigation/README.md) |
| [`maps/`](maps/) | 导航与建图地图 | 当前默认地图在此 |
| [`urdf/`](urdf/) | 实车几何和传感器外参 | 由 `robot_state_publisher.launch` 加载 |
| [`scripts/`](scripts/) | RF1 协议烟测工具 | 不属于日常导航入口 |
| `src/` | `clb_base_node` 等旧底盘源码 | 历史底盘链仍可能引用 |

## 当前装配关系

| 功能 | 入口 |
| --- | --- |
| PC TEB 导航 | `launch/nav/navigation_406_rf1_teb.launch` |
| PC 传统规划回退 | `launch/nav/navigation_406_rf1.launch` |
| AMCL | `launch/amcl.launch` |
| RF1 最小硬件链 | `launch/bringup_rf1_min.launch` |
| RPLIDAR | `launch/lidar/rplidar.launch` |
| IMU | `launch/core/imu_only.launch` |
| 建图 | `launch/slam/slam_406_lsm.launch` |
| URDF / TF | `launch/robot_state_publisher.launch` |

## 修改约束

1. `map -> odom -> base_link -> sensor` 必须只有一条有效 TF 发布链。
2. 树莓派硬件链和 PC 解算链不可同时发布同名 `/odom`。
3. 速度输出默认走 `/cmd_vel_nav`，再经过安全门到 `/cmd_vel`。
4. footprint、URDF 几何、TEB 距离和 RF1 转向几何修改后需要联合实测。
5. 新增 launch、地图或脚本时同步更新对应子目录 README。
