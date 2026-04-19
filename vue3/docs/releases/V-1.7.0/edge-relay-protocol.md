# V-1.7.0 edge-relay 协议第一版

## 职责边界

`edge-relay` 是云端联调 transport，不替代本地 `rosbridge`。

- 前端只找 backend
- backend 暴露 REST `/api/ros/*` 给前端
- Pi 侧 edge-relay 主动连接 backend 的 `/edge/ros`
- Pi 侧 relay 本地负责把 backend 下行控制转成 ROS `/cmd_vel`

## WebSocket 入口

正式入口：

```text
wss://api.hzhhds.top/edge/ros
```

本地模拟入口：

```text
ws://127.0.0.1:<PORT>/edge/ros
```

## 认证

首帧必须是 `hello`。backend 不使用 `verifyClient` 做主认证；upgrade 只做路径分发。

连接后若 `EDGE_HELLO_TIMEOUT_MS` 内没有收到合法 `hello`，backend 直接关闭连接。

设备 token 不明文入库，`EdgeDevice.tokenHash` 使用 bcrypt。

## 上行 hello

```json
{
  "op": "hello",
  "deviceId": "csrpi-001",
  "token": "<DEVICE_TOKEN>",
  "transport": "edge-relay",
  "topics": {
    "cmd_vel": "/cmd_vel",
    "odom": "/odom",
    "imu": "/imu/data",
    "scan": "/scan"
  },
  "capabilities": ["manual_control", "odom", "imu", "scan_summary"]
}
```

backend 校验通过后回复：

```json
{
  "op": "hello_ack",
  "deviceId": "csrpi-001",
  "accepted": true,
  "ts": 1710000000000
}
```

## 上行 heartbeat

```json
{
  "op": "heartbeat",
  "deviceId": "csrpi-001",
  "ts": 1710000000000
}
```

heartbeat 只更新在线状态和最近心跳时间，不触发复杂副作用。

## 上行 telemetry

```json
{
  "op": "telemetry",
  "deviceId": "csrpi-001",
  "odom": {},
  "imu": {},
  "scanSummary": {},
  "ts": 1710000000000
}
```

本轮只接受 `scanSummary`，禁止上传全量 LaserScan。

## 下行 manual_control

由现有 `/api/ros/cmd-vel` 或 `/api/ros/manual-preset` 触发：

```json
{
  "op": "manual_control",
  "seq": 123,
  "vx": 0.1,
  "vy": 0,
  "wz": 0,
  "holdMs": 400
}
```

## 下行 stop

零速命令或 hold 到期时发送：

```json
{
  "op": "stop",
  "seq": 124
}
```

## 当前限制

- 第一版只支持单个在线目标设备
- 同一 `deviceId` 重连时，backend 关闭旧连接并使用新连接
- 不做设备管理 UI / API
- 不把 `/edge/ros` 暴露给前端使用
