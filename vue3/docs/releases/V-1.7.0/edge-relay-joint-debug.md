# V-1.7.8 edge-relay 联调诊断记录

## 当前 backend 结论

本地 backend 已切到：

```text
APP_PROFILE=public-edge
ROS_TRANSPORT=edge-relay
EDGE_RELAY_ENABLED=true
EDGE_RELAY_PATH=/edge/ros
```

本地联调入口：

```text
ws://10.117.77.190:3000/edge/ros
```

当前本地 `csrpi-001` token 已由现场单独传递给 C 线，不写入仓库文档。

## V 线已验证

V 线用同一入口和同一 token 进行本机标准 hello 测试，backend 可返回：

```json
{
  "op": "hello_ack",
  "deviceId": "csrpi-001",
  "accepted": true
}
```

这说明：

- backend profile 生效
- `/edge/ros` path 生效
- `csrpi-001` 已在本地 DB 中启用
- token hash 校验可通过
- backend 不要求 `Authorization: Bearer <token>`
- backend 以首帧 `hello.token` 为设备认证依据

## 现场日志暴露的问题

backend 日志显示来自 `10.117.77.84` 的连接同时出现两类事件：

```text
[edge-relay] hello-accepted {"deviceId":"csrpi-001", ...}
[edge-relay] reject {"code":"EDGE_HELLO_REQUIRED","message":"first message must be hello", ...}
[edge-relay] replace-session {"deviceId":"csrpi-001", ...}
[edge-relay] connection-close {"code":4000,"reason":"EDGE_DEVICE_REPLACED", ...}
```

这说明当前不是单纯 token 错，也不是 path/profile 未生效。

更可能的问题是 Pi 侧存在以下至少一种情况：

- 同一个 `deviceId=csrpi-001` 被多个 WebSocket 连接同时使用
- 某些 WebSocket 连接建立后第一帧不是 `hello`
- 发送 heartbeat / telemetry 的任务早于 hello_ack 启动
- reconnect loop 没有等待旧 socket 完全关闭，导致新连接顶掉旧连接
- send loop 和 recv loop 各自创建了独立连接

## C 线需要确认 / 修改

Pi 侧 edge-relay 必须满足：

1. 每个 `deviceId` 同一时间只保留一条 WebSocket 连接。
2. `on_open` 后第一帧必须立即发送 `hello`。
3. 收到 `hello_ack.accepted=true` 后，才能启动 heartbeat / telemetry。
4. heartbeat / telemetry / recv loop / command loop 必须复用同一条 WebSocket。
5. reconnect 前必须停止旧 socket 的所有 send / recv task。
6. reconnect 需要退避，不能一秒内并发拉起多条连接。
7. 必须打印 close code 和 reason。

首帧格式固定为：

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

## V 线热修

本轮 backend 已新增 edge-relay 诊断日志：

- `upgrade-accepted`
- `connection-open`
- `hello-accepted`
- `reject`
- `replace-session`
- `connection-close`

后续联调时，双方必须同时对齐：

- Pi 侧 close code / reason
- backend `[edge-relay]` 日志
- 当前 active deviceId
- 当前是否有多个 edge-relay 进程或多个 socket task

## 当前判断

V 线 backend 当前链路不是“完全没收到”，而是已经收到并接受过 Pi 的合法 hello。

当前主要阻塞更偏向 C 线 edge-relay 连接生命周期管理：需要收敛为单连接、hello_ack 后再启动其它上行任务。
