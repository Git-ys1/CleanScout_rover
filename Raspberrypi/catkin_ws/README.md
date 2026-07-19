# CleanScout catkin_ws

这是 CleanScout 的 ROS Noetic catkin 工作空间。顶层 shell 文件保留在工作空间根目录，
因为现有树莓派部署使用固定绝对路径，且部分脚本会互相调用。

## 工作空间结构

| 路径 | 内容 | 是否入库 |
| --- | --- | --- |
| [`src/`](src/) | ROS 包源码 | 是 |
| `build/` | catkin 构建中间产物 | 否 |
| `devel/` | catkin 开发空间 | 否 |
| `bags/` | 实车 rosbag | 否 |
| `*.sh` | 环境、启动、诊断和维护入口 | 是 |
| [`NETWORK.md`](NETWORK.md) | 随身 Wi-Fi 固定拓扑与手机热点回退规则 | 是 |

## 当前推荐流程

| 步骤 | 树莓派 | PC |
| --- | --- | --- |
| 0. 网络 | `./cleanscout_network.sh` | `./cleanscout_network.sh` |
| 1. 环境 | `source ./use_cleanscout_pi.sh` | `source ./use_cleanscout_pc.sh`，默认连接 Pi `.108` |
| 2. 硬件 | `./run_robot_hardware_multifunction.sh` | 不启动重复硬件节点 |
| 3A. 导航 | 保持硬件链运行 | `./start_pc_full_navigation.sh` |
| 3B. 建图 | 保持硬件链运行 | `./start_pc_mapping_mode2.sh` |
| 4. 收尾 | 按需运行清理脚本 | 建图时可先 `./save_map.sh` |

## Shell 文件总表

### 当前主链

| 文件 | 运行端 | 用途 | 备注 |
| --- | --- | --- | --- |
| [`cleanscout_network.sh`](cleanscout_network.sh) | 双端 | 统一解析随身 Wi-Fi 与手机热点地址 | 可直接运行做只读检查 |
| [`use_cleanscout_pi.sh`](use_cleanscout_pi.sh) | 树莓派 | 加载 Noetic/catkin，设置本机 ROS master | 应使用 `source` |
| [`run_robot_hardware_multifunction.sh`](run_robot_hardware_multifunction.sh) | 树莓派 | RF1、雷达、安全门、风机/顶盖、edge relay | 当前硬件主入口；要求注入 edge token |
| [`use_cleanscout_pc.sh`](use_cleanscout_pc.sh) | PC | 发现 PC/Pi 地址并设置分布式 ROS 环境 | 可由 PC 入口自动加载 |
| [`start_pc_full_navigation.sh`](start_pc_full_navigation.sh) | PC | 启动 odom、地图、AMCL、move_base/TEB、RViz | 当前导航主入口 |
| [`start_pc_mapping_mode2.sh`](start_pc_mapping_mode2.sh) | PC | 启动 odom、gmapping 和 RViz | 当前建图主入口 |
| [`save_map.sh`](save_map.sh) | PC 优先 | 保存 `/map` 到 `clbrobot/maps` | 可传地图名 |

### 专项与实车工具

| 文件 | 运行端 | 用途 | 风险 / 前提 |
| --- | --- | --- | --- |
| [`calibrate_rf1_turn.sh`](calibrate_rf1_turn.sh) | PC | 对比编码器、生产 odom 与纯激光匹配角度 | 会控制小车转动 |
| [`send_nav_cmd.sh`](send_nav_cmd.sh) | PC | 向指定速度话题发送有限时长 Twist | 会控制小车运动 |
| [`test_rf1_cmd_vel.sh`](test_rf1_cmd_vel.sh) | 树莓派 | 拉起 RF1 最小链并做速度自检 | 会控制车轮 |
| [`record_bench_stack.sh`](record_bench_stack.sh) | 树莓派 | 记录雷达、TF、RF1 调试话题 | 输出到 `bags/` |
| [`run_rf1_core_stack.sh`](run_rf1_core_stack.sh) | 树莓派 | 分阶段启动 RF1 核心 | 不含完整导航 |
| [`run_edge_relay.sh`](run_edge_relay.sh) | 树莓派 | 单独启动 edge relay | 依赖已有 ROS master |
| [`run_edge_relay_remote_only.sh`](run_edge_relay_remote_only.sh) | 树莓派 | RF1 + edge relay 远程控制链 | 专项远程模式 |

### 诊断与清理

| 文件 | 用途 | 影响范围 |
| --- | --- | --- |
| [`check_ros_master.sh`](check_ros_master.sh) | 检查 ROS 环境、进程、11311 端口和 master 通信 | 只读 |
| [`check_openclaw_gateway.sh`](check_openclaw_gateway.sh) | 检查 OpenClaw 命令、配置和用户服务 | 只读 |
| [`clean_mapping_nav_sessions.sh`](clean_mapping_nav_sessions.sh) | 结束导航/建图/RF1/传感器相关进程 | 当前优先清理入口 |
| [`clean_edge_relay_sessions.sh`](clean_edge_relay_sessions.sh) | 仅结束 edge relay | 定向清理 |
| [`clean_rf1_web_sessions.sh`](clean_rf1_web_sessions.sh) | 清理旧 RF1 Web 联调链 | 使用 `pkill -9`，谨慎 |
| [`clean_ros_sessions.sh`](clean_ros_sessions.sh) | 清理旧全栈 ROS 进程 | 范围很广，谨慎 |

### 历史兼容

| 文件 | 原用途 | 当前判断 |
| --- | --- | --- |
| [`run_nav_and_multifunction_demo.sh`](run_nav_and_multifunction_demo.sh) | 树莓派本机联合导航与多功能演示 | 保留旧成熟演示链 |
| [`run_slam_mapping.sh`](run_slam_mapping.sh) | 树莓派本机全量建图 | 已由 PC 建图第二模式取代 |
| [`run_mapping_406_lsm.sh`](run_mapping_406_lsm.sh) | 树莓派本机 LSM + gmapping | 早期集成入口 |
| [`start_desk_navigation.sh`](start_desk_navigation.sh) | 桌面地图和旧轮桥导航 | 旧硬件/地图兼容 |

## 常用覆盖项

| 变量 | 默认值 | 作用 |
| --- | --- | --- |
| `CLEANSCOUT_NETWORK_MODE` | `portable_wifi` | 默认固定地址；设为 `phone_hotspot` 恢复旧动态子网逻辑 |
| `CLEANSCOUT_PI_HOST` | 空 | 显式覆盖 PC 使用的 ROS master 主机 |
| `CLEANSCOUT_PC_HOST` | 空 | 显式覆盖 Pi 使用的本地 backend 主机 |
| `NAV_LAUNCH` | `navigation_406_rf1_teb.launch` | PC 导航入口，可切传统规划器 |
| `MAP_FILE` | `407-5.22-2120.yaml` | 导航地图 |
| `ODOM_K_M` | `0.1987` | PC 端轮速反解角速度 |
| `RF1_CMD_K_M` | `0.1987` | 树莓派命令侧转向几何 |
| `START_RVIZ` | `1` | 是否启动 RViz |

## C-4.1.7 无 IMU 正式数据链

MPU6050 已因机械结构调整永久退出正式硬件。当前入口不会等待 `/imu/data`，也不会
发布虚假 IMU 数据。树莓派硬件主入口保持以下顺序：

```text
清理旧会话 -> roscore -> robot_state_publisher -> RF1 -> 等待 /rf1/vel
-> RPLIDAR -> 等待 /scan -> cmd_vel_safety_gate -> 风机/顶盖 -> edge-relay
```

PC 建图：

```text
/rf1/vel -> rf1_vel_to_odom.py -> /odom + odom->base_link
/scan + TF + /odom -> gmapping -> /map
```

PC 导航：

```text
/rf1/vel -> rf1_vel_to_odom.py -> /odom + odom->base_link
/map + /scan + TF + /odom -> AMCL -> move_base/TEB -> /cmd_vel_nav
```

`EDGE_DEVICE_TOKEN` 只能由本机安全配置注入；为空时硬件主入口会在启动任何 ROS
进程前明确退出。

## 维护规则

1. 新增顶层脚本时，必须在本页登记运行端、用途和运动风险。
2. 当前主链脚本不得静默改名或移动；若要重构，先消除绝对路径并更新部署说明。
3. 实车会运动的脚本必须有限时长、失联停车或安全门保护。
4. 生成目录、rosbag 和 `/tmp` 日志不得提交。
5. ROS 包说明见 [`src/README.md`](src/README.md)。
6. 网络地址只在 [`cleanscout_network.sh`](cleanscout_network.sh) 维护，完整规则见 [`NETWORK.md`](NETWORK.md)。
