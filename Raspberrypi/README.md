# Raspberrypi 线成果总览

本目录记录 CleanScout 项目在树莓派 / ROS 上位机方向上的阶段性成果、正式入口与关键脚本。  
当前这条线已经从早期的树莓派本机全量解算，逐步推进到“树莓派减压、电脑参与解算、后端与导航兼容共存”的新阶段架构。

## 一、当前成果概览

当前已经形成三条可区分的成果链：

1. 旧成熟联合演示链
2. 当前导航与多功能第二模式
3. 当前建图第二模式

这三条链路覆盖了：

1. 底盘串口桥接
2. IMU 与雷达接入
3. 风机 / 继电器 / 顶盖多功能控制
4. edge-relay 与后端联调
5. RViz 导航
6. 编码器 odom 导航解算
7. 电脑侧 gmapping 建图
8. `/cmd_vel_nav -> cmd_vel_safety_gate -> /cmd_vel` 安全速度链

## 二、当前最重要的能力提升

相对早期版本，当前树莓派线已经完成的关键升级包括：

### 1. 树莓派减压

- 不再强制把所有导航解算压在树莓派本机
- 电脑已经可以参与导航与建图解算
- 为后续更复杂算法和报告展示预留算力空间

### 2. 导航与后端控制兼容

- 后端与电脑导航统一走 `/cmd_vel_nav`
- 最终统一经过 `cmd_vel_safety_gate`
- 已解决“后端空闲持续发 0 速度，压住导航”的历史 bug

### 3. 后端控制从脉冲式升级为翻转式

- 再次点击同方向即可停下
- 停下时只发一次 0 速度
- 停下后不再持续发 0

### 4. 形成当前第二模式

- 树莓派只负责硬件、安全门控、edge-relay
- 电脑负责编码器 odom 导航解算与 RViz
- 后端与电脑共用 `/cmd_vel_nav`

### 5. 形成当前建图第二模式

- 树莓派只跑硬件和安全链
- 电脑端运行 `rf1_vel_to_odom.py`
- 电脑端发布 `/odom` 和 `odom -> base_link`
- 电脑端运行 gmapping 建图
- 地图可直接保存到电脑本地工作区

### 6. 明确第二模式转弯参数归属

- 树莓派第二模式使用 `RF1_CMD_K_M` 控制 `/cmd_vel` 到四轮目标速度
- 电脑两个第二模式入口使用 `ODOM_K_M` 从 `/rf1/vel` 反解 `/odom`
- 2026-06-06 实车基线为 `RF1_CMD_K_M=0.1987`、`RF1_MIN_WHEEL_MS=0.0`、
  `ODOM_K_M=0.1987`，都可在启动前覆盖
- 可运行 `catkin_ws/calibrate_rf1_turn.sh left|right [wz] [seconds]` 复测；
  工具会比较编码器、去零偏 IMU 和纯雷达匹配角，并在 `/tmp` 保存 rosbag
- 标定换算：`新 ODOM_K_M = 旧 ODOM_K_M * odom 显示角度 / 实际角度`

### 7. 接入第一版 URDF / robot_state_publisher

- 已根据实车测量值建立第一版几何模型
- 已将 `laser` / `imu_link` 纳入 `robot_state_publisher`
- 当前成熟导航链已开始用 URDF 替代原始手写静态 TF
- 为后续统一 TF、碰撞边界、传感器外参和可研报告图示打下基础

## 三、当前常用入口

### 1. 旧成熟联合演示链

树莓派执行：

```bash
cd /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
source ./use_cleanscout_pi.sh
bash ./run_nav_and_multifunction_demo.sh
```

用途：

- 树莓派本机同时跑导航与多功能
- 用于保留旧成熟演示链能力

### 2. 导航与多功能第二模式

树莓派执行：

```bash
cd /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
source ./use_cleanscout_pi.sh
EDGE_CMD_TOPIC=/cmd_vel_nav EDGE_ODOM_TOPIC=/odom EDGE_ALLOW_MANUAL_CONTROL=true EDGE_PUBLISH_CMD_VEL=true EDGE_TOGGLE_MOTION_ENABLED=true EDGE_ALLOW_FAN_CONTROL=true ./run_robot_hardware_multifunction.sh
```

电脑执行：

```bash
cd /home/yusu/Work/CleanScout_rover/Raspberrypi/catkin_ws
./start_pc_full_navigation.sh
```

用途：

- 当前新阶段导航主链
- 树莓派减压
- 电脑参与导航解算
- 后端与导航共存

### 3. 建图第二模式

树莓派执行：

```bash
cd /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
source ./use_cleanscout_pi.sh
EDGE_CMD_TOPIC=/cmd_vel_nav EDGE_ODOM_TOPIC=/odom EDGE_ALLOW_MANUAL_CONTROL=true EDGE_PUBLISH_CMD_VEL=true EDGE_TOGGLE_MOTION_ENABLED=true EDGE_ALLOW_FAN_CONTROL=true ./run_robot_hardware_multifunction.sh
```

电脑执行：

```bash
cd /home/yusu/Work/CleanScout_rover/Raspberrypi/catkin_ws
./start_pc_mapping_mode2.sh
```

地图保存：

```bash
./save_map.sh
```

用途：

- 当前新阶段建图主链
- 电脑参与建图解算
- 建图结果默认保存在电脑本地 `clbrobot/maps`

## 四、当前关键代码成果

当前树莓派线关键成果主要集中在：

1. `run_robot_hardware_multifunction.sh`
2. `run_nav_and_multifunction_demo.sh`
3. `start_pc_full_navigation.sh`
4. `start_pc_mapping_mode2.sh`
5. `src/csrpi_edge_relay/scripts/edge_relay.py`
6. `src/csrpi_base_bridge/scripts/cmd_vel_safety_gate.py`
7. `src/csrpi_base_bridge/scripts/rf1_vel_to_odom.py`
8. `src/clbrobot_project/clbrobot/launch/nav/navigation_406_rf1.launch`
9. `src/clbrobot_project/clbrobot/launch/slam/slam_406_lsm.launch`

## 五、当前发布说明

当前发布时要注意：

1. 不提交 `Raspberrypi/catkin_ws/build/`
2. 不提交 `Raspberrypi/catkin_ws/devel/`
3. 地图文件是否纳入版本库需要按阶段确认
4. 正式汇报 / 可研报告时，应优先展示第二模式与建图第二模式成果
5. 当前补充合并发布为 `C-4.1.2`，记录见
   `releases/C-4.1.2/C-4.1.2_supplemental_merge_release.md`

## 六、参考文档

建议优先阅读：

1. `docs/树莓派端_退休交接书.md`
2. `桌面/交流使用.txt` 中同步下来的当前联调口径
3. `Raspberrypi/releases/` 下历史归档
