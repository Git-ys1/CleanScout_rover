# CleanScout 导航参数维护指南

本文档对应 ROS Noetic PC 端导航配置。自 `C-4.1.4` 起，参数文件使用
UTF-8 中文注释说明单位、耦合关系和调参方向。

## 当前默认链路

```text
start_pc_full_navigation.sh
  -> rf1_vel_to_odom.py (/rf1/vel -> /odom + odom->base_link)
  -> navigation_406_rf1_teb.launch
     -> map_server
     -> amcl.launch
     -> move_base_teb.xml
        -> costmap_mecanum_params.yaml
        -> local_costmap_params.yaml
        -> global_costmap_params.yaml
        -> teb_local_planner_params.yaml
        -> move_base_teb_params.yaml
```

`C-4.1.7` 起导航入口固定使用编码器里程计，不再提供 IMU 或
`USE_LASER_SCAN_MATCHER` 隐藏分支。定位输入为地图、`/scan`、`/odom` 和 TF。

控制输出：

```text
move_base/TEB
  -> /cmd_vel_nav
  -> cmd_vel_safety_gate
  -> /cmd_vel
  -> cmdvel_to_rf1
  -> RF1
```

当前雷达后半场被机械结构遮挡，活动安全策略为：

- TEB 不以倒车方向初始化，并强烈惩罚反向轨迹
- `cmd_vel_safety_gate` 默认硬裁掉全部负 `vx`
- 麦克纳姆横移和 `vx/vy` 组合斜向运动保持启用
- `move_base` 不执行自动原地旋转清障
- 正常路径转向仍然保留，启动前必须人工确认车体四周有完整旋转余量

`costmap_obstacles_behind_robot_dist` 只会使用已经进入 costmap 的障碍，不能让
物理盲区获得感知能力。完整实测证据见
[`../../../../../../docs/teb_rear_blind_sector_and_km_recalibration.md`](../../../../../../docs/teb_rear_blind_sector_and_km_recalibration.md)。

传统 `TrajectoryPlannerROS` 仅作为回退链保留：

```bash
NAV_LAUNCH=navigation_406_rf1.launch ./start_pc_full_navigation.sh
```

## 文件职责

| 文件 | 当前职责 |
| --- | --- |
| `teb_local_planner_params.yaml` | TEB 速度、轨迹、障碍物、优化权重、多拓扑和恢复参数 |
| `move_base_teb_params.yaml` | move_base 主循环频率、超时、规划器插件和恢复开关 |
| `costmap_mecanum_params.yaml` | 机器人 footprint、激光障碍源和共用 costmap 参数 |
| `local_costmap_params.yaml` | 局部滚动窗口、刷新频率和局部膨胀层 |
| `global_costmap_params.yaml` | 静态全局地图、刷新频率和全局膨胀层 |
| `move_base_teb.xml` | TEB 参数装配顺序及 odom frame/topic 最终覆盖 |
| `base_local_planner_params.yaml` | 传统 TrajectoryPlannerROS 回退参数 |
| `move_base_params.yaml` | 传统回退链的 move_base 主循环参数 |
| `move_base.xml` | 传统回退参数装配入口 |
| `../../launch/amcl.launch` | AMCL 粒子、激光模型、全向里程计模型和更新阈值 |

## 参数覆盖顺序

`move_base_teb.xml` 先把 `costmap_mecanum_params.yaml` 分别加载到
`global_costmap` 和 `local_costmap`，随后加载两个专用 costmap 文件。
因此：

- 全局 `inflation_radius` 最终取 `global_costmap_params.yaml`
- 局部 `inflation_radius` 最终取 `local_costmap_params.yaml`
- footprint 和 `/scan` 障碍源来自 `costmap_mecanum_params.yaml`
- `local_costmap/global_frame` 最终由启动参数覆盖
- `TebLocalPlannerROS/odom_topic` 最终由启动参数覆盖

排查“文件改了但线上没变化”时，必须先执行：

```bash
rosparam get /move_base
rosparam get /amcl
```

不要只根据 YAML 文本判断实际运行值。

## 必须成组调整

### 机器人外形与避障距离

以下参数共同决定能否通过窄道以及离墙距离：

```text
costmap_mecanum_params.yaml: footprint
local_costmap_params.yaml: inflation_radius, cost_scaling_factor
global_costmap_params.yaml: inflation_radius, cost_scaling_factor
teb_local_planner_params.yaml: min_obstacle_dist, inflation_dist
```

修改任意一项后，至少回归：

- 正向通过窄道
- 横移与斜向靠近障碍，重点检查盲区边界回波
- 原地旋转四角碰撞风险
- 局部绕障后回归全局路径

### 速度与加速度

规划速度和执行速度涉及三层：

```text
teb_local_planner_params.yaml
cmd_vel_safety_gate.launch
bringup_rf1_min.launch / cmdvel_to_rf1.py
```

安全门和 RF1 转换层是最终硬限制。TEB 上限更高时，优化器会假设一种
底盘实际无法完整执行的速度模型；修改后必须观察局部轨迹跟踪误差。

### 定位与里程计

以下配置必须与真实底盘运动形式一致：

```text
amcl.launch: odom_model_type, odom_alpha1..5
start_pc_full_navigation.sh: ODOM_TOPIC, ODOM_K_M
navigation_406_rf1_teb.launch: odom_frame_id, odom_topic
```

麦克纳姆底盘使用 `omni-corrected`，TEB 与安全门保留横移和斜向能力。
切回 `diff` 会忽略横向运动模型。

### TEB 多拓扑

`C-4.1.4` 启用 Homotopy Class Planning。主要 CPU 开销由以下参数控制：

```text
max_number_classes
max_number_plans_in_current_class
roadmap_graph_no_samples
no_inner_iterations
no_outer_iterations
```

当前 vendored TEB `0.9.1` 对路网采样数量存在两个历史键名：

```text
roadmap_graph_samples
roadmap_graph_no_samples
```

前者供启动读取代码使用，后者供 dynamic_reconfigure 使用。配置中必须保持
同值。

## 中文注释兼容性

YAML 的 `#` 注释和 XML 的 `<!-- -->` 注释不会进入 ROS 参数值。ROS Noetic
在 Ubuntu 20.04/Python 3 环境能够读取 UTF-8 注释。

本轮没有向树莓派同步带中文注释的导航 YAML/TEB/URDF；板端只同步了不含中文的
`cmd_vel_safety_gate.py`，并最小更新 RF1 活动入口中的 `K_M` 默认值。以后若要部署
PC 导航参数到其他机器，应先执行：

```bash
python3 -c 'import yaml; yaml.safe_load(open("teb_local_planner_params.yaml", encoding="utf-8"))'
xmllint --noout move_base_teb.xml
roslaunch --nodes clbrobot navigation_406_rf1_teb.launch
```

## 发布前检查

```bash
cd /home/yusu/Work/CleanScout_rover/Raspberrypi/catkin_ws
source use_cleanscout_pc.sh

roslaunch --nodes clbrobot navigation_406_rf1_teb.launch
rosparam get /move_base/base_local_planner
rosparam get /move_base/TebLocalPlannerROS
rosparam get /move_base/global_costmap/footprint
rosparam get /amcl/odom_model_type
```

涉及行为参数的版本必须在发布记录中写明：

- 修改前后值
- 实车观察结果
- 是否同步树莓派
- 尚未覆盖的路线或环境
