# V-1.6.0 backend-centric ROS relay RFC

## RFC 结论

“ROS 主动连 backend、backend 做中心”的方向可行，但不是 `rosbridge` 原生能力。

`rosbridge` 当前角色是：

```text
backend / 非 ROS 客户端 -> rosbridge -> ROS
```

如果要改成：

```text
ROS / 树莓派 -> backend
```

则 C 线需要在树莓派侧新增一个 outbound relay / agent。

## 新 transport 草案

新增可选 transport 名称：

```text
edge-relay
```

默认状态：

- 不启用
- 不替换当前 `rosbridge`
- 仅作为联合评审草案

## Pi 侧职责草案

树莓派侧新增 relay 服务，负责：

- 本地连接 ROS 或本地 `rosbridge`
- 主动向 backend 发起 outbound HTTP / WS 长连接
- 上送心跳和在线状态
- 上送 `/odom` 摘要
- 上送 `/imu/data` 摘要
- 上送 `/scan` 摘要或节流数据
- 接收 backend 下发的 `ManualControlCommand`
- 本地转成 `/cmd_vel`

## backend 职责草案

backend 负责：

- 维护设备连接会话
- 校验设备 token
- 接收 relay 上送状态
- 缓存遥测摘要
- 将管理员按钮或 OpenClaw 意图统一转为 `ManualControlCommand`
- 按设备连接状态下发命令

## 安全要求

relay 不允许裸连：

- 必须使用设备 token 或等价认证
- backend 不向前端暴露设备 token
- 命令仍走 `ManualControlCommand`
- 默认速率和 `holdMs` 继续受 backend 限制

## 与现有 rosbridge 的关系

当前已跑通链路继续保留：

```text
frontend -> backend -> rosbridge -> ROS
```

`edge-relay` 只是第二 transport：

```text
frontend -> backend <- edge-relay <- ROS / Pi
```

因此：

- V 线本轮不改真实控制链路
- C 线可先评审，不必立即实现
- 后续如果 C 线实现 relay，V 线再单独立项切换或并存

## 待 C 线评审

1. relay 使用 HTTP 长轮询、WebSocket 还是 SSE
2. relay 是否本地连 ROS 原生 topic，还是继续连本机 rosbridge
3. telemetry 摘要频率
4. `/scan` 是否只上传摘要，不上传完整扫描
5. 设备 token 的生成、轮换和吊销方式
6. 离线重连与命令幂等规则
