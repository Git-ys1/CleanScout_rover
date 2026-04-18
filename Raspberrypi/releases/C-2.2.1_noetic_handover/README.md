# C-2.2.1 Noetic 接管归档总览

## 1. 文档定位

- 关联任务：`C-2.2.1`
- 归档目标：把当前树莓派 `Noetic` 镜像的环境审计、workspace 结构、launch 入口与驱动假设正式入库
- 性质：接管与归档，不是功能开发

本目录是 `C-2.2.1` 的正式树莓派归档入口。  
原始日志来自本地 staging 目录 `docs/未确认-新文件/`，本轮只做正式副本归档，不改写原日志内容。

## 2. 当前系统结论

- 系统：`Ubuntu 20.04.3 LTS`
- 内核：`Linux 5.4.0-1052-raspi`
- 架构：`arm64`
- ROS：`Noetic 1.15.11`
- 用户：`clbrobot`
- SSH：`enabled + active`
- 网络：当前主链路为 `wlan0`
- 当前 `ROS_MASTER_URI / ROS_IP / ROS_HOSTNAME`：`10.11.191.84`

## 3. 当前工作空间

- 主工作空间：`/home/clbrobot/catkin_ws`
- 次级工作空间：`/home/clbrobot/goolge_ws`

当前判断：

- `catkin_ws` 是当前主接管入口
- `goolge_ws` 仅在审计日志中出现，当前保留为“存在但角色未定”的次级 workspace

## 4. 当前已识别入口

关键 launch 入口已确认存在：

- `clbrobot/launch/bringup.launch`
- `clbrobot/launch/navigate.launch`
- `clbrobot/launch/slam/lidar_slam.launch`
- `clbrobot/launch/lidar/rplidar.launch`

当前串口设备已确认：

- `/dev/ttyAMA0`
- `/dev/ttyS0`

## 5. 原始日志清单

本轮正式归档如下原始日志：

- `raw/C-2.1.8_audit/00_basic.txt`
- `raw/C-2.1.8_audit/01_ros_env.txt`
- `raw/C-2.1.8_audit/02_ws_dirs.txt`
- `raw/C-2.1.8_audit/03_ws_tree.txt`
- `raw/C-2.1.8_audit/05_docs_and_scripts.txt`
- `raw/C-2.1.8_audit/06_runtime_io.txt`
- `raw/C-2.1.9/C-2.1.9_launch_files.txt`
- `raw/C-2.1.9/C-2.1.9_grep_core.txt`
- `raw/C-2.1.10/C-2.1.10_driver_grep.txt`

## 6. 当前接管边界

- 本轮只做归档、研究报告、边界更新说明、入口审查
- 不推进 `STM32`
- 不改 `Tyler_1` / `UNO + AFMotor` 底层 API
- 不直接改 `SLAM / navigation / EKF` 代码
- 树莓派 Noetic 栈作为上位/中位接管对象先入库审查

## 7. 关联文档

- `docs/PLAN/C-2.2.1.md`
- `docs/SYSTEM/C-2.2.1_takeover_research_report.md`
- `docs/HARDWARE/C-2.2.1_hardware_boundary_update.md`
- `docs/SOFTWARE/C-2.2.1_noetic_entry_review.md`
