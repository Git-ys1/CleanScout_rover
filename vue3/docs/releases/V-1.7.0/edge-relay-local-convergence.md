# V-1.7.9 edge-relay 本地联调收敛结论

## 本轮结论

V-1.7.9 本地 edge-relay 联调已收敛。

当前链路：

```text
前端网页 -> backend public-edge -> /edge/ros WebSocket -> edge-relay(Pi) -> ROS -> OpenRF1
```

已达到本轮验收口径：

- Pi 侧能主动连接 backend `/edge/ros`
- backend 能接受 `csrpi-001` 的 `hello`
- backend 能维持 edge-relay 在线状态
- backend 能收到 heartbeat / telemetry
- 前端网页能通过现有 `/api/ros/*` 控制小车
- 前端没有直连树莓派、rosbridge 或 `/edge/ros`

## 当前 backend 状态

本地 backend 当前运行口径：

```text
APP_PROFILE=public-edge
ROS_TRANSPORT=edge-relay
EDGE_RELAY_ENABLED=true
EDGE_RELAY_PATH=/edge/ros
```

接口状态复核：

```text
transport=edge-relay
connected=true
edgeRelayConnected=true
edgeDeviceId=csrpi-001
lastRelayError=
odomAvailable=true
imuAvailable=true
```

`scanAvailable=false` 当前不阻塞本轮收敛；第一版 edge-relay 只要求 scan 摘要能力，不要求全量 LaserScan。后续若 C 线需要前端展示 scan 摘要，再单独补字段与 UI。

## 日志依据

backend 日志已持续出现：

```text
[edge-relay] upgrade-accepted
[edge-relay] connection-open
[edge-relay] hello-accepted {"deviceId":"csrpi-001", ...}
```

此前出现的 `EDGE_HELLO_REQUIRED` 与 `EDGE_DEVICE_REPLACED` 已用于定位 Pi 侧多连接 / 首帧顺序问题；当前联调结果显示协议顺序已收敛到可用状态。

## 本轮冻结边界

本轮冻结的是本地局域网 edge-relay 联调通过，不等同于公网云端 WSS 正式上线。

仍未冻结：

- `wss://api.hzhhds.top/edge/ros` 公网真实连通
- Nginx / TLS / systemd 生产实机部署
- 多设备并发管理
- scan 摘要 UI
- 生产 token 轮换机制

## 后续建议

下一轮进入公网云端前，必须重新生成生产 token，并在云端数据库中 seed 对应 `EdgeDevice`。本地联调 token 不应直接复用到公网。
