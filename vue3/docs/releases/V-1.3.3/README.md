---
version: V-1.3.3
based_on_branch: main
branch_source: GitHub branches page + origin/main fetch verification
published_to_root: vue3/
published_at_commit: 9bebbda8b797be6a2adf2145f8eea98bb84e1d38
---

# V-1.3.3 以 main 为基线的第一版 ROS 接入层施工

## 本轮结论

本轮以 `main` 为统一真相分支完成第一版 ROS 接入层施工，不推翻当前 `vue3/` 基线，只补三件事：

- backend 正式新增 `ROS adapter`
- 首页新增 ROS 状态卡片
- 管理员台新增 ROS 控制台与遥测摘要

本轮继续保持职责边界：

- `ROS`：固定控制、最小状态摘要、后续导航语义层接入
- `OpenClaw`：自然语言对话、意图转命令
- 前端统一只接 `backend`

## main 真实基线

当前以 `main` 的公开树莓派工作区为依据，已核实存在：

- `Raspberrypi/catkin_ws/src/.../bench_full_stack.launch`
- `Raspberrypi/catkin_ws/src/.../slam/lidar_slam_pi.launch`
- `Raspberrypi/catkin_ws/src/.../nav_base_stack.launch`
- `Raspberrypi/catkin_ws/src/.../desk_map_navigation.launch`
- `Raspberrypi/catkin_ws/src/csrpi_base_bridge/scripts/wheel_bridge.py`
- `Raspberrypi/catkin_ws/src/csrpi_base_bridge/scripts/enc_to_raw_vel.py`
- `Raspberrypi/catkin_ws/src/csrpi_base_bridge/scripts/cmdvel_to_wheels.py`

因此，本轮冻结后的 V 线判断为：

- 当前 ROS 主接入假设不再是旧的 `bringup.launch`
- 当前接入基线改为 `bench_full_stack.launch` 与 `slam/lidar_slam_pi.launch`
- `main` 现已足够证明 ROS 控制 / SLAM / 导航主线存在
- `main` 当前未发现 `rosbridge_suite`、`rosbridge_websocket`、`roslibjs` 这类现成 Web 转发层
- V 线本轮补的是 `backend ROS adapter`，不是前端直连 ROS

## 本轮改动

### backend ROS adapter

新增目录：

```text
backend/src/integrations/ros/
├─ index.js
├─ transport.js
├─ rosbridgeClient.js
├─ mapper.js
├─ stateCache.js
└─ dto.js
```

冻结内容：

- `ROS_ENABLED`、`ROS_TRANSPORT`、`ROSBRIDGE_URL`、`ROS_*_TOPIC`
- 优先 transport：`mock / rosbridge`
- 默认 topic：`/cmd_vel`、`/odom`、`/imu/data`、`/scan`
- 默认短持续控制参数：`ROS_CMD_REPEAT_HZ=10`、`ROS_CMD_DEFAULT_HOLD_MS=400`
- backend 控制模型：`holdMs + repeatHz`，到期自动补一次 `stop`

新增接口：

- `GET /api/integrations/ros/status`
- `POST /api/ros/cmd-vel`
- `POST /api/ros/manual-preset`
- `GET /api/ros/telemetry/summary`

新增内部统一控制 DTO：

```text
ManualControlCommand
- source: "admin" | "ros" | "openclaw"
- linear
- angular
- holdMs
- metadata
```

### frontend

新增：

- `src/api/ros.js`
- `src/stores/ros.js`

页面更新：

- 首页新增 ROS 状态卡片，显示 transport / connected / heartbeat / cmd_vel topic
- 管理员页在原“接入状态”分区内扩展 ROS 状态与 ROS 控制台
- 管理员固定控制按钮：前进、后退、左转、右转、左平移、右平移、停止
- 对话页继续只承载自然语言平面，不混入 ROS 固定控制

## 当前职责边界

当前 backend 架构冻结为：

```text
前端（uni-app）
        |
        v
backend
   ├─ ROS adapter（固定控制 / 状态摘要）
   └─ OpenClaw adapter（自然语言 / 意图控制）
        |
        v
树莓派 ROS / OpenClaw Gateway / 设备侧
```

规则：

- 管理员按钮控制统一先映射成 `ManualControlCommand`
- 当前管理员固定控制优先走 ROS adapter
- 对话页仍优先保留 `mock / OpenClaw` 平面
- 下一轮树莓派若补齐 `rosbridge_websocket`，backend 直接切 `ROS_TRANSPORT=rosbridge`

## 验证

已完成：

- `cmd /c npm.cmd run build:h5`
- backend 新增 ROS 文件语法检查通过
- `admin / 123456` 登录后可调用：
  - `GET /api/integrations/ros/status`
  - `POST /api/ros/cmd-vel`
  - `POST /api/ros/manual-preset`
  - `GET /api/ros/telemetry/summary`
- 当前 `ROS_TRANSPORT=mock` 下：
  - ROS 状态接口返回 `transport=mock`
  - 管理员 preset 可返回 `accepted=true`
  - 普通用户调用 ROS 控制接口返回 `AUTH_ADMIN_REQUIRED`

## 未完成项

本轮明确未做：

- 真实树莓派 `rosbridge` 联调
- 真实 `ws://<raspberrypi-ip>:9090` 连通性验证
- ROS topic 真实订阅时序确认
- 真正设备状态接入和真实底盘控制验收

下一轮树莓派联调合同继续按以下口径准备：

- 优先补 `rosbridge_websocket`
- backend 默认请求 `ws://<raspberrypi-ip>:9090`
- 如果 C 线不采用 `rosbridge`，则需树莓派侧自行补一层本地 HTTP / WS bridge

## 发布纪律

- 本轮先在 V 线自测分支完成冻结：`feature/v-1.3.3-ros-adapter-main-baseline`
- 后续发布到主项目时，只把 `vue3/` 作为 supplement merge 补充进 `main`
- 不覆盖、不替换、不修改 C 线树莓派源码
