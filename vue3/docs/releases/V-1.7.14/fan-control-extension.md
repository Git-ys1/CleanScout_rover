# V-1.7.14 双风机控制扩展冻结

## 本轮结论

本轮已将双风机能力接入当前 `V` 线前后端，保持现有结构不变：

```text
前端 -> backend -> rosbridge / edge-relay -> ROS -> 风机桥
```

本轮冻结的三项业务能力：

1. 风机系统总开关
2. 双风机 PWM 调节
3. 双风机 RPM 回传查看

本轮仍然不暴露：

1. lid 舵机角度单独控制
2. relay 单独开关
3. 原始 FG 通道作为产品态显示

## backend API

### 1. 读取风机状态

```text
GET /api/device/fans/state
```

返回结构：

```json
{
  "enabled": true,
  "fanA": { "pwm": 35.0, "rpm": 1200.0 },
  "fanB": { "pwm": 35.0, "rpm": 1180.0 },
  "lidOpen": true,
  "summary": "enabled=true lid_open=true relay=on ...",
  "lastUpdate": "2026-04-25T12:34:56.000Z"
}
```

### 2. 设置风机总开关

```text
POST /api/device/fans/enable
```

请求体：

```json
{
  "enabled": true
}
```

### 3. 设置双风机 PWM

```text
POST /api/device/fans/pwm
```

请求体：

```json
{
  "fanA": 35.0,
  "fanB": 35.0
}
```

限制：

- `fanA` / `fanB` 范围固定为 `0 ~ 100`
- 仅管理员可调用 `enable` 与 `pwm`
- 所有已登录用户可读取 `state`

## transport 冻结

本轮已将双风机能力接入三种 transport：

1. `mock`
2. `rosbridge`
3. `edge-relay`

### rosbridge 主题口径

```text
/fans/enable
/fan_a/pwm_percent
/fan_b/pwm_percent
/fan_a/rpm
/fan_b/rpm
/fan_lid/state
/fans/state_summary
```

### edge-relay 下行帧

风机总开关：

```json
{
  "op": "fan_enable",
  "seq": 201,
  "enabled": true
}
```

双风机 PWM：

```json
{
  "op": "fan_pwm",
  "seq": 202,
  "fanA": 35.0,
  "fanB": 35.0
}
```

### edge-relay 上行帧

推荐并入现有 `telemetry`：

```json
{
  "op": "telemetry",
  "deviceId": "csrpi-001",
  "fans": {
    "enabled": true,
    "fanA": { "pwm": 35.0, "rpm": 1200.0 },
    "fanB": { "pwm": 35.0, "rpm": 1180.0 },
    "lidOpen": true,
    "summary": "enabled=true lid_open=true relay=on ..."
  },
  "ts": 1710000000000
}
```

也接受独立 fan-only 帧：

```json
{
  "op": "fan_telemetry",
  "deviceId": "csrpi-001",
  "enabled": true,
  "fanA": { "pwm": 35.0, "rpm": 1200.0 },
  "fanB": { "pwm": 35.0, "rpm": 1180.0 },
  "lidOpen": true,
  "summary": "enabled=true lid_open=true relay=on ...",
  "ts": 1710000000000
}
```

## 前端冻结

本轮前端入口固定在首页：

- 新增 `双风机系统` 卡片
- 管理员可操作：
  - 开启 / 关闭风机系统
  - 调节风机 A / 风机 B PWM
- 普通用户只读查看：
  - 风机 A / B 当前 PWM
  - 风机 A / B 回传 RPM
  - lid 状态
  - 最近摘要

## 验收口径

本轮前端与 backend 已完成静态接入和构建验证：

1. `node --check` 通过风机相关 backend 文件
2. `build:h5:local` 通过
3. `build:mp-weixin:local` 通过

真实联调时，应至少验证：

1. `GET /api/device/fans/state` 可读到回传 RPM
2. `POST /api/device/fans/enable` 可切风机系统开关
3. `POST /api/device/fans/pwm` 可更新双风机 PWM
4. 首页风机卡片可看到 RPM 与摘要同步刷新
