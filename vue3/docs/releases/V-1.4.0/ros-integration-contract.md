# V-1.4.0 ROS 联调合同

## 当前职责边界

当前 V 线对 ROS 与 OpenClaw 的职责边界冻结为：

- `ROS`：固定控制、最小状态摘要、后续底盘 / 建图 / 导航语义层接入
- `OpenClaw`：自然语言对话、意图转命令、后续智能编排
- 前端不直接连树莓派，不直接连 ROS master，不直接连 OpenClaw Gateway
- 当前统一结构：`uni-app 前端 -> backend -> ROS adapter / OpenClaw adapter -> 树莓派 / 设备侧`

## backend 当前依赖的 ROS 环境变量

当前 `backend` 已冻结以下环境变量：

- `ROS_ENABLED`
- `ROS_TRANSPORT`
- `ROSBRIDGE_URL`
- `ROS_CMD_VEL_TOPIC`
- `ROS_ODOM_TOPIC`
- `ROS_IMU_TOPIC`
- `ROS_SCAN_TOPIC`
- `ROS_CMD_REPEAT_HZ`
- `ROS_CMD_DEFAULT_HOLD_MS`
- `ROS_RECONNECT_DELAY_MS`

默认值口径：

```text
ROS_ENABLED=true
ROS_TRANSPORT=mock
ROSBRIDGE_URL=ws://127.0.0.1:9090
ROS_CMD_VEL_TOPIC=/cmd_vel
ROS_ODOM_TOPIC=/odom
ROS_IMU_TOPIC=/imu/data
ROS_SCAN_TOPIC=/scan
ROS_CMD_REPEAT_HZ=10
ROS_CMD_DEFAULT_HOLD_MS=400
ROS_RECONNECT_DELAY_MS=1000
```

## 期望的接入方式

当前 backend 优先要求树莓派侧提供：

- `rosbridge`

如果 C 线不采用 `rosbridge`，则必须提供：

- 等价的 `HTTP / WS bridge`

也就是说，backend 只接受“非 ROS 客户端可消费的桥接层”，不假设公网 backend 能直接说 ROS master 原生协议。

## 默认端口与 topic

当前默认 rosbridge 端口固定为：

```text
9090
```

当前 backend 期待的 topic 固定为：

- `/cmd_vel`
- `/odom`
- `/imu/data`
- `/scan`

## backend 当前行为

当前 `backend/src/integrations/ros/` 已实现：

- 通过 `/cmd_vel` publish 控制
- 订阅 `/odom`
- 订阅 `/imu/data`
- 订阅 `/scan`
- `mock / rosbridge` 双 transport 切换

当前默认 transport 仍为：

```text
ROS_TRANSPORT=mock
```

也就是说，本轮还没有进入真实树莓派联调态；下一轮只要树莓派侧补齐 rosbridge 或等价 bridge，backend 就可以从 `mock` 切到真实链路。

## 网络前提

**如果 backend 在 ECS / 公网，而树莓派在手机热点、NAT 或内网后面，必须额外提供隧道、VPN 或反向桥，不能假设公网 backend 可以直接访问树莓派 `9090`。**

当前默认可接受方案：

- `SSH` 隧道
- `Tailscale / ZeroTier / VPN`
- C 线自建的反向 `HTTP / WS bridge`

## 下一轮联调前需要树莓派侧确认的内容

1. 是否采用 `rosbridge`
2. 若采用，实际地址是否可从 backend 到达
3. 若不采用，替代 `HTTP / WS bridge` 的协议与地址
4. `cmd_vel / odom / imu / scan` 是否仍沿用当前默认 topic
5. 实机控制的安全阈值是否仍使用当前默认：
   - 前后：`±0.20 m/s`
   - 平移：`±0.15 m/s`
   - 转向：`±0.35 rad/s`
   - `holdMs=400`

## 当前结论

本轮文档冻结的目的不是开始实机控制，而是先把 backend 对树莓派 ROS 联调的“合同面”写清。下一轮树莓派端只要按本合同提供桥接入口，V 线无需再重构前端和 backend 边界。
