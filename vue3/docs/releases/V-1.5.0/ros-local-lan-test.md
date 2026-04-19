# V-1.5.0 ROS 本地局域网联调记录

## 联调目标

本轮 ROS 验收只针对：

```text
本机前端 / 本机 backend -> 局域网树莓派 rosbridge
```

不处理：

- NAT 穿透
- FRP / VPN
- ECS 公网连树莓派

## 当前联调地址

- 本机局域网 IP：`10.117.77.190`
- 树莓派 rosbridge：`ws://10.117.77.84:9090`
- 当前默认 topic：
  - `/cmd_vel`
  - `/odom`
  - `/imu/data`
  - `/scan`

## backend 启动口径

当前本地联调必须使用 `deploy/env/vline-backend.local-lan.env.example` 对应口径：

```text
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
ROS_TRANSPORT=rosbridge
ROSBRIDGE_URL=ws://10.117.77.84:9090
```

说明：

- `CORS_ALLOWED_ORIGINS` 只保证 H5 浏览器本地调试可用
- 微信小程序 / App 不依赖这项配置
- 本轮不允许把 `ROS_TRANSPORT` 留在 `mock`

## 本轮验证步骤

1. 在本机启动 backend，并确认运行时环境为：

```text
ROS_TRANSPORT=rosbridge
ROSBRIDGE_URL=ws://10.117.77.84:9090
```

2. 登录管理员账号 `admin / 123456`
3. 验证：
   - `GET /api/integrations/ros/status`
   - `GET /api/ros/telemetry/summary`
4. 在管理员页或等价接口调用中下发低速预设命令：
   - `forward`
   - `backward`
   - `turn_left`
   - `turn_right`
   - `strafe_left`
   - `strafe_right`
   - `stop`

## 通过标准

本轮通过必须同时满足：

- `transport=rosbridge`
- `connected=true`
- `lastHeartbeatAt` 有值
- `telemetry/summary` 中至少有真实时间戳更新
- 管理员低速预设命令成功返回
- 全过程没有落回 `mock`

## 本机实测结果

本机于 `2026-04-18` 已完成一次真实局域网联调，结果如下：

- `GET /api/integrations/ros/status`
  - `transport=rosbridge`
  - `connected=true`
  - `rosbridgeUrl=ws://10.117.77.84:9090`
- `GET /api/ros/telemetry/summary`
  - `odomAvailable=true`
  - `imuAvailable=true`
  - `scanAvailable=true`
  - `lastOdomAt`、`lastImuAt`、`lastScanAt` 均已更新
- 管理员低速预设命令 `forward`
  - 返回 `accepted=true`
  - `transport=rosbridge`
  - `scheduledStopAt` 正常生成

说明：

- 初次建立 `rosbridge` 连接后，遥测时间戳可能会比状态接口慢几秒到位
- 本轮验收以“真实 rosbridge 已连接且 telemetry 有更新”为准，不以 `mock` 代替

## 当前结论口径

这份文档冻结的是“本地局域网 ROS 真联调”的执行合同。后续如果要做公网 backend + 树莓派远程互通，需要单独补 NAT / 隧道 / VPN 方案，不能把本轮局域网结果直接外推成公网可用。
