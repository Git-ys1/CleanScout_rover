# V2.1.0 OpenClaw PC Worker 联调冻结

## 元数据

```text
version=V2.1.0
scope=OpenClaw PC Worker chat bridge
frontend=CleanScout 自有对话页
backend=REST + /ws/agents
worker=tools/pc-openclaw-worker
ros_actions=not_enabled
```

## 本轮结论

本轮接入的是 `OpenClaw` 能力，不嵌入 `OpenClaw Dashboard`。产品展示与用户交互继续走 CleanScout 自己的前端。

冻结链路：

```text
前端 -> 云端 backend <- WebSocket -> pc-openclaw-worker -> 本机 OpenClaw Gateway
```

本轮只打通自然语言对话，不接 ROS 控制、不发导航 goal、不控制风机或底盘。

## 云端 backend 新增入口

前端调用：

```text
POST /api/openclaw/chat
GET /api/openclaw/status?deviceId=cleanscout-001
```

PC worker 长连接：

```text
wss://api.hzhhds.top/ws/agents
```

第一版 agent 消息：

```text
AGENT_REGISTER
AGENT_HEARTBEAT
OPENCLAW_CHAT_REQUEST
OPENCLAW_CHAT_RESULT
```

## backend env

`public-edge` profile 需要新增：

```text
AGENT_WS_ENABLED=true
AGENT_WS_PATH=/ws/agents
AGENT_SHARED_SECRET=<现场生成的 worker 接入 token>
AGENT_HEARTBEAT_TIMEOUT_MS=30000
OPENCLAW_ROUTE_MODE=pc-worker
OPENCLAW_CHAT_TIMEOUT_MS=60000
```

说明：

- `AGENT_SHARED_SECRET` 只用于校验 PC worker 是否允许接入云端 backend。
- `OPENCLAW_GATEWAY_TOKEN` 不进云端 backend，不写入前端。
- 云端 backend 不直接访问 `127.0.0.1:18789`，只通过在线 worker 转发。

## 云端 backend 部署操作

云端后端更新代码仍使用既有脚本：

```bash
cd /opt/CleanScout_rover/vue3
sudo bash scripts/update-backend.sh
```

如果服务器源码目录不是 `/opt/CleanScout_rover/vue3`，先用下面命令确认：

```bash
sudo find /opt -path '*/vue3/scripts/update-backend.sh' -print
```

云端 `/etc/vline-backend.env` 只填写 worker 接入 token，不填写 OpenClaw Gateway token：

```bash
sudo cp /etc/vline-backend.env /etc/vline-backend.env.bak.$(date +%Y%m%d%H%M%S)
sudo nano /etc/vline-backend.env
```

需要确认存在：

```text
APP_PROFILE=public-edge
AGENT_WS_ENABLED=true
AGENT_WS_PATH=/ws/agents
AGENT_SHARED_SECRET=<现场生成的 worker 接入 token>
AGENT_HEARTBEAT_TIMEOUT_MS=30000
OPENCLAW_ROUTE_MODE=pc-worker
OPENCLAW_CHAT_TIMEOUT_MS=60000
```

改完后重启并检查：

```bash
sudo systemctl restart vline-backend
sudo systemctl status vline-backend --no-pager
curl -sS https://api.hzhhds.top/api/system/health
```

注意：`AGENT_SHARED_SECRET` 必须和 PC worker 的 `CLOUD_AGENT_TOKEN` 完全一致。

## PC worker

目录：

```text
tools/pc-openclaw-worker/
```

本机 `.env` 示例：

```text
DEVICE_ID=cleanscout-001
AGENT_ID=pc-yusu-main
AGENT_TYPE=pc-openclaw-worker
CLOUD_WS_URL=wss://api.hzhhds.top/ws/agents
CLOUD_AGENT_TOKEN=<与 backend AGENT_SHARED_SECRET 一致>
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_GATEWAY_TOKEN=<本机 OpenClaw Gateway token>
OPENCLAW_MODEL=openclaw/default
OPENCLAW_API_MODE=chat
```

启动：

```bash
cd tools/pc-openclaw-worker
npm ci
npm run start
```

Ubuntu PC 本机建议先跑 probe，再连接云端：

```bash
cd tools/pc-openclaw-worker
npm ci
npm run probe
npm run start
```

probe 只验证本机 `OpenClaw Gateway`，不会连接云端。`npm run start` 才会连接 `wss://api.hzhhds.top/ws/agents`。

PC worker `.env` 中：

- `CLOUD_AGENT_TOKEN` 填云端 backend 的 `AGENT_SHARED_SECRET`。
- `OPENCLAW_GATEWAY_TOKEN` 填 Ubuntu PC 本机 OpenClaw Gateway token。
- 这两个 token 都不提交到公开仓库。

## Nginx

`api.hzhhds.top` 需要同时反代：

```text
/api/       -> http://127.0.0.1:3000
/edge/ros   -> WebSocket -> http://127.0.0.1:3000
/ws/agents  -> WebSocket -> http://127.0.0.1:3000
```

`/ws/agents` 必须透传：

```text
Upgrade
Connection
```

并设置较长 `proxy_read_timeout`。

## 前端行为

对话页继续使用 CleanScout 自己的聊天 UI：

- 显示 `pc-openclaw-worker` 在线 / 离线
- 显示设备 `cleanscout-001`
- 显示 worker `pc-yusu-main`
- 聊天发送走 `/api/openclaw/chat`
- 失败时显示中文错误，不伪装 OpenClaw 成功

前端不显示、不保存、不传递：

```text
OPENCLAW_GATEWAY_TOKEN
OpenClaw Dashboard URL
127.0.0.1:18789
```

## 验收口径

通过标准：

1. PC 运行 OpenClaw Gateway。
2. PC 运行 `pc-openclaw-worker`。
3. 云端 backend `/api/openclaw/status` 显示 `pcWorkerOnline=true`。
4. 前端对话页输入“你现在是谁？”。
5. 返回内容来自本机 OpenClaw Gateway。
6. 输入“开始巡检”时只返回计划或确认提示，不触发 ROS / 设备动作。

## 后续轮次

下一轮再接结构化意图和执行器：

- 导航类：`pc-ros-executor`
- 设备类：继续走 `pi-edge-relay`
- 对话类：继续走 `pc-openclaw-worker`

本轮不得把 OpenClaw、ROS、edge-relay 混成一个节点。
