# CleanScout Raspberrypi / ROS Noetic

本目录保存 CleanScout 小车的 ROS Noetic 工作空间、PC/树莓派启动入口、地图和阶段发布记录。
`C-4.1.5` 起采用分层 README 管理目录；启动脚本暂不搬家，避免破坏实车上的绝对路径和脚本调用链。

## 当前基线

| 项目 | 当前口径 |
| --- | --- |
| 操作系统 / ROS | Ubuntu + ROS Noetic |
| 构建系统 | catkin |
| 树莓派职责 | RF1 底盘、雷达、安全门、多功能硬件、edge relay |
| PC 职责 | 里程计解算、建图、AMCL、move_base、TEB、RViz |
| 导航基线 | `C-4.1.4` 参数，TEB 多拓扑为默认局部规划器 |
| 文档治理基线 | `C-4.1.5` |
| 网络基线 | `C-4.1.6`，默认随身 Wi-Fi 固定拓扑 |
| 无 IMU 硬件基线 | `C-4.1.7`，MPU6050 永久退出正式运行链 |
| 默认地址 | Pi `.108`、OrangePi `.148`、PC `.222`，网段 `192.168.8.0/24` |
| 速度安全链 | `/cmd_vel_nav -> cmd_vel_safety_gate -> /cmd_vel -> RF1` |
| 转向几何基线 | `RF1_CMD_K_M=0.1987`，`ODOM_K_M=0.1987` |

## 目录导航

| 路径 | 内容 | 维护建议 |
| --- | --- | --- |
| [`catkin_ws/`](catkin_ws/) | ROS 工作空间和全部运行入口 | 日常启动从这里开始 |
| [`catkin_ws/NETWORK.md`](catkin_ws/NETWORK.md) | 随身 Wi-Fi 与旧手机热点网络基线 | 切换网络或排查 ROS master 时先读 |
| [`catkin_ws/src/`](catkin_ws/src/) | 自研与 vendored ROS 包 | 新包必须在 `src/README.md` 登记 |
| [`catkin_ws/src/clbrobot_project/clbrobot/`](catkin_ws/src/clbrobot_project/clbrobot/) | 整车 launch、参数、地图、URDF | 导航配置的主要入口 |
| [`maps/`](maps/) | 早期桌面地图 | 历史兼容，不是当前默认地图目录 |
| [`releases/`](releases/) | 每轮阶段封存与验证记录 | 发布时新增版本目录和索引 |
| [`../docs/`](../docs/) | 项目级交接、测量和设计文档 | 先读交接书，再改实车链 |

## 日常入口

以下命令均从 `Raspberrypi/catkin_ws` 目录执行。

| 场景 | 运行端 | 命令 | 状态 |
| --- | --- | --- | --- |
| 硬件与多功能主链 | 树莓派 | `source ./use_cleanscout_pi.sh && ./run_robot_hardware_multifunction.sh` | 当前主链 |
| 完整导航 | PC | `./start_pc_full_navigation.sh` | 当前主链，默认 TEB |
| 建图 | PC | `./start_pc_mapping_mode2.sh` | 当前主链 |
| 保存地图 | PC | `./save_map.sh [map_name]` | 当前工具 |
| 转向标定 | PC | `./calibrate_rf1_turn.sh left\|right [wz] [seconds]` | 实车专项，会动车 |
| 旧联合演示 | 树莓派 | `./run_nav_and_multifunction_demo.sh` | 历史兼容 |

完整的 24 个 shell 文件、运行端、风险和用途见
[`catkin_ws/README.md`](catkin_ws/README.md)。

## 数据流

| 链路 | 数据方向 |
| --- | --- |
| 速度命令 | PC/后端 `/cmd_vel_nav` -> 树莓派安全门 -> `/cmd_vel` -> RF1 |
| 编码器里程计 | RF1 `/rf1/vel` -> PC `rf1_vel_to_odom.py` -> `/odom` + `odom -> base_link` |
| 定位 | 地图 + `/scan` + odom TF -> AMCL -> `map -> odom` |
| 导航 | move_base/TEB -> `/cmd_vel_nav` |
| 建图 | `/scan` + odom TF -> gmapping -> `/map` |

MPU6050 已因机械结构调整从实车正式硬件中移除。当前入口不会启动、等待、订阅或
模拟 `/imu/data`；硬件主链启动前必须从本机安全配置向环境注入 `EDGE_DEVICE_TOKEN`。

## 状态约定

| 标记 | 含义 |
| --- | --- |
| 当前主链 | 日常联调和阶段汇报优先使用 |
| 专项工具 | 标定、录包、单模块运行等明确用途 |
| 诊断 / 清理 | 不提供业务能力，只用于定位或结束会话 |
| 历史兼容 | 为复现旧阶段保留，不应成为新功能依赖 |
| 待退役 | 已知链路不完整，确认无引用后再删除 |

## 发布与安全

| 规则 | 说明 |
| --- | --- |
| 不提交生成物 | `catkin_ws/build/`、`catkin_ws/devel/`、rosbag、运行日志 |
| 不直接搬顶层脚本 | 多个脚本仍使用树莓派绝对路径并互相调用 |
| 中文注释范围 | PC 端参数和文档可使用；同步树莓派前仍需做 UTF-8/XML/YAML 验证 |
| 实车命令 | 标定、手动速度和 RF1 自检前必须架空或留出安全区域 |
| 凭据 | 新代码只通过环境变量或本机配置注入，不在 README 中记录令牌 |

## 推荐阅读顺序

1. [`../docs/树莓派端_退休交接书.md`](../docs/树莓派端_退休交接书.md)
2. [`catkin_ws/README.md`](catkin_ws/README.md)
3. [`catkin_ws/NETWORK.md`](catkin_ws/NETWORK.md)
4. [`catkin_ws/src/README.md`](catkin_ws/src/README.md)
5. [`catkin_ws/src/clbrobot_project/clbrobot/param/navigation/README.md`](catkin_ws/src/clbrobot_project/clbrobot/param/navigation/README.md)
6. [`releases/C-4.1.7/C-4.1.7_remove_mpu6050_from_active_stack.md`](releases/C-4.1.7/C-4.1.7_remove_mpu6050_from_active_stack.md)
