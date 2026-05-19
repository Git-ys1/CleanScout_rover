# 快捷控制台闭环控制联调申请书

## 申请目的

当前 V 线首页快捷控制台已经可以通过：

```text
前端 -> backend -> edge-relay -> ROS -> OpenRF1
```

下发 `manual_control / stop`，实现前进、后退、转向、平移、停止等基础遥控。

但当前控制方式本质仍是：

```text
人工按钮 -> 短时速度指令 -> 到期 stop
```

这属于开环控制。V 线现在需要升级为“闭环控制台”，即控制动作必须基于底盘实际反馈进行修正、确认和安全停止。

## 当前结论

闭环控制主体不应放在前端或云端 backend。

原因：

- 前端和云端 backend 不具备实时控制周期保障。
- WebSocket / 公网 / 手机热点链路存在抖动和延迟，不适合作为控制环路。
- V 线只能可靠承担目标下发、状态展示、权限控制、操作记录和联调验收。
- 真正闭环必须依赖树莓派 ROS、编码器、IMU、里程计、下位机速度环或导航栈。

因此本轮任务主体应由树莓派 / C 线负责，V 线配合接口对齐。

## 闭环分层定义

为避免误解，本申请将闭环控制分成四层：

```text
L0 电机 / 轮速闭环
下位机根据编码器或电机反馈维持目标轮速。

L1 底盘速度闭环
树莓派或下位机根据 odom / encoder / IMU 修正 vx / vy / wz，使实际速度贴近目标速度。

L2 动作基元闭环
例如前进 0.3m、左转 30°、平移 0.2m，系统根据 odom / IMU 判断完成并自动 stop。

L3 导航闭环
通过 move_base / 导航栈到达目标点。
```

当前 V 线快捷控制台至少需要 L1；如果要让按钮具备“点一下完成一个稳定动作”的体验，则需要 L2。

## 当前 V 线已有能力

V 线当前已经具备：

- 登录与管理员权限控制
- 首页快捷控制台
- `POST /api/ros/manual-preset`
- `POST /api/ros/cmd-vel`
- `GET /api/integrations/ros/status`
- `GET /api/ros/telemetry/summary`
- edge-relay 长连接
- `manual_control / stop` 下行帧
- 心跳、遥测、风机等状态回传展示

当前 V 线不会直接接 ROS master，不会直接接下位机。

## 请求 C 线 / 树莓派侧完成的事项

### 1. 明确当前已有闭环层级

请确认当前 OpenRF1 链路中已经实现了哪一层闭环：

- 是否已有下位机轮速闭环
- 是否已有底盘速度闭环
- `/cmd_vel` 下发后，实际 `vx / vy / wz` 是否会根据反馈修正
- 当前 `odom / imu / wheel feedback` 是否稳定可用于动作完成判断

### 2. 提供闭环控制执行入口

建议树莓派侧提供一个新的闭环动作入口，优先在 edge-relay 协议内扩展，而不是让 V 线自己做控制环。

建议下行帧：

```json
{
  "op": "closed_loop_control",
  "seq": 301,
  "mode": "preset",
  "preset": "forward",
  "target": {
    "distanceM": 0.3,
    "yawDeg": 0,
    "durationMs": 0
  },
  "limits": {
    "maxLinear": 0.12,
    "maxAngular": 0.25,
    "timeoutMs": 3000
  }
}
```

也可以由 C 线拍板改成 ROS service / action，再由 edge-relay 转接。

### 3. 提供闭环状态回传

V 线需要展示闭环执行状态，建议回传：

```json
{
  "op": "control_status",
  "deviceId": "csrpi-001",
  "seq": 301,
  "mode": "closed_loop",
  "state": "running",
  "preset": "forward",
  "progress": 0.42,
  "error": null,
  "feedback": {
    "linearSpeed": 0.08,
    "angularSpeed": 0.0,
    "distanceM": 0.12,
    "yawDeg": 0.4
  },
  "ts": 1710000000000
}
```

状态建议固定为：

```text
pending
running
succeeded
failed
timeout
stopped
emergency_stop
```

### 4. 提供安全策略

树莓派侧必须明确：

- 最大线速度
- 最大角速度
- 单次动作最大距离
- 单次动作最大角度
- 超时自动 stop
- edge 断联自动 stop
- emergency stop 是否高优先级

V 线不应自行猜这些安全阈值。

### 5. 提供联调 topic / 日志观测点

请 C 线提供最小观测集合，例如：

```bash
rostopic echo /cmd_vel
rostopic echo /odom
rostopic echo /imu/data
rostopic echo /rf1/status
rostopic echo /rf1/cmdvel_debug
rostopic echo /rf1/wheel_target_ms
```

如果新增闭环节点，也请提供：

```bash
rostopic echo /rf1/closed_loop_status
```

或等价日志输出。

## V 线配合事项

C 线确认协议后，V 线可以配合完成：

- 首页快捷控制台增加“开环 / 闭环”模式显示
- 管理员操作按钮切换到闭环 API
- backend 增加 `closed_loop_control` 下行帧
- telemetry 增加 `control_status` 缓存
- 前端展示运行中、成功、失败、超时、急停等状态
- 保留当前 `manual_control / stop` 作为调试与兜底通道

## 不建议的方案

不建议 V 线直接做以下事情：

- 前端读取 odom 后自行循环发速度
- 云端 backend 根据公网 telemetry 计算控制误差
- 用 H5 / 小程序定时器实现闭环
- 在网络抖动环境下由前端判断动作完成

这些方案都不满足设备控制安全性和实时性要求。

## 第一阶段验收标准

建议 C 线第一阶段先完成以下闭环动作：

- 前进固定距离
- 后退固定距离
- 左转固定角度
- 右转固定角度
- 停止 / 急停

最小验收：

1. V 线下发一个闭环动作请求。
2. 树莓派侧返回 `running`。
3. 底盘执行动作。
4. 树莓派侧根据反馈自动 stop。
5. 树莓派侧返回 `succeeded / failed / timeout`。
6. 断开 edge-relay 时底盘不会继续运动。

## 责任边界

本轮闭环控制任务主体：

```text
C 线 / 树莓派侧负责：控制环、反馈读取、误差计算、安全停止、状态回传。
```

V 线负责：

```text
V 线负责：入口、权限、API 对齐、状态展示、操作记录、联调验收。
```

## 当前结论

快捷控制台要从开环升级为闭环，不能只改前端按钮，也不能只改 backend。

本质上需要树莓派侧提供稳定的闭环控制能力，然后 V 线把它接入现有：

```text
前端 -> backend -> edge-relay -> 树莓派闭环控制节点
```

链路。
