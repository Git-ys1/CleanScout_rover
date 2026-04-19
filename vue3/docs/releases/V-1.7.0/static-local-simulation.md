# V-1.7.0 静态与本地 edge-relay 模拟记录

## 本轮前提

实验室关闭，真实 Pi / ROS / OpenRF1 不在线，因此本轮不做真实云端 ROS 联调。

本轮验证目标是：

- backend 能启动 `public-edge` profile
- `/edge/ros` 能接受模拟 Pi 的 `hello / heartbeat / telemetry`
- 现有 `/api/ros/manual-preset` 能在 `edge-relay` transport 下下发控制帧

## 模拟结果

本地模拟使用临时 SQLite、临时 env、临时端口 `3300`，验证结果：

```json
{
  "helloAck": true,
  "transport": "edge-relay",
  "edgeRelayConnected": true,
  "edgeDeviceId": "csrpi-001",
  "odomAvailable": true,
  "imuAvailable": true,
  "scanAvailable": true,
  "commandAccepted": true,
  "commandTransport": "edge-relay",
  "receivedControlOps": ["manual_control", "manual_control", "stop"]
}
```

说明：

- 第二个 `manual_control` 来自 backend 的 `holdMs + repeatHz` 短持续控制
- `stop` 来自 hold 到期后的自动补停
- 测试结束后临时 DB、临时 env、临时日志和 3300 进程均已清理

## Prisma 说明

当前环境中 `npx prisma db push` 对临时 SQLite 报 `Schema engine error`，但 `prisma validate` 与 `prisma migrate diff --from-empty --to-schema-datamodel` 均可通过。

为完成本地静态模拟，本轮使用 `migrate diff` 生成 SQL，并用 Python `sqlite3` 建立临时库。该处理只用于本地验证，不改变生产部署建议。

生产部署仍按既有纪律使用：

```text
npx prisma migrate deploy
```

## 未完成

- 未确认真实 Pi edge-relay 程序已连接
- 未确认真实 `/cmd_vel` 已被 Pi 转发到 ROS
- 未做公网 WSS 实际连通测试
