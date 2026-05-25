# OpenClaw CleanScout 接入设计

## 1. 当前边界

本轮只做 **PC 侧 OpenClaw 接入与能力桥准备**，不做云端后端开发，不做底盘下位机开发。

当前分工：

1. 后端工程师负责云端接口、WebSocket agent 接入、账户与消息流转
2. ROS / 树莓派工程师负责导航、建图、状态话题、设备能力落地
3. OpenClaw 工程师负责本机 Gateway、PC worker、OpenClaw 本地能力调用与协议对齐

## 2. 本轮目标

本轮目标不是“让 OpenClaw 直接控车”，而是先把下面这条链路准备好：

```text
云端后端
    ↓
pc-openclaw-worker
    ↓
本机 OpenClaw Gateway (127.0.0.1:18789)
    ↓
返回结果给云端后端
```

## 3. 当前 OpenClaw 正确定位

OpenClaw 当前定位为：

1. 上层智能入口
2. 自然语言理解层
3. 任务编排层
4. 运维问答与日志总结层

OpenClaw 当前不直接承担：

1. PWM
2. 编码器闭环
3. `/cmd_vel` 实时连续控制
4. 底盘底层驱动

## 4. 本轮由本地 PC 侧独立交付的内容

### 4.1 Gateway 侧

1. OpenClaw Gateway 常驻运行
2. 本机可访问 `http://127.0.0.1:18789`
3. 本机可使用 token 调用 OpenClaw

### 4.2 Worker 侧

新增 `tools/pc-openclaw-worker/`，用于承接：

1. 读取本地 `.env`
2. 主动连接云端 WebSocket
3. 接收后端下发的 `OPENCLAW_CHAT_REQUEST`
4. 转发到本机 OpenClaw Gateway
5. 把 `OPENCLAW_CHAT_RESULT` 回传后端

### 4.3 后续 ROS 能力桥预留

第一轮不直接做 ROS executor，但要在协议里预留能力名，例如：

1. `get_rover_status`
2. `get_ros_summary`
3. `start_navigation`
4. `cancel_navigation`
5. `start_mapping`
6. `set_fan_pwm`
7. `summarize_fault_logs`

## 5. 与后端联调合同对齐的消息结构

### 5.1 worker 注册

```json
{
  "type": "AGENT_REGISTER",
  "agentType": "pc-openclaw-worker",
  "deviceId": "cleanscout-001",
  "agentId": "pc-yusu-main",
  "capabilities": [
    "openclaw.chat",
    "openclaw.status",
    "openclaw.models"
  ],
  "version": "0.1.0"
}
```

### 5.2 worker 心跳

```json
{
  "type": "AGENT_HEARTBEAT",
  "agentId": "pc-yusu-main",
  "deviceId": "cleanscout-001",
  "ts": 1770000000000
}
```

### 5.3 后端发起对话请求

```json
{
  "type": "OPENCLAW_CHAT_REQUEST",
  "requestId": "req-001",
  "conversationId": "conv-001",
  "messages": [
    {
      "role": "user",
      "content": "你现在能控制 CleanScout 吗？"
    }
  ]
}
```

### 5.4 worker 返回结果

```json
{
  "type": "OPENCLAW_CHAT_RESULT",
  "requestId": "req-001",
  "conversationId": "conv-001",
  "ok": true,
  "reply": "我可以作为 CleanScout 的智能调度助手工作，但实际控制需要经过后端权限校验和设备执行器。",
  "raw": {
    "model": "openclaw/default"
  }
}
```

## 6. OpenClaw 本地访问合同

本机 Worker 只访问：

```text
http://127.0.0.1:18789
```

第一轮必须支持：

1. `GET /v1/models`
2. `POST /v1/chat/completions`

## 7. 当前阶段不做的事

1. 不把 OpenClaw Dashboard 直接当产品前端
2. 不把 OpenClaw token 交给用户前端
3. 不让 OpenClaw 直接控制 `/cmd_vel`
4. 不把 OpenClaw 直接塞进 ROS 节点
5. 不碰 F 盘下位机闭环代码

## 8. 下一步接口对接方式

一旦后端给出：

1. `CLOUD_WS_URL`
2. `CLOUD_AGENT_TOKEN`
3. `deviceId`
4. WebSocket 认证方式

本地 worker 即可直接开始联调。
