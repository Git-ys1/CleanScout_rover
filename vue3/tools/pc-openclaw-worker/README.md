# pc-openclaw-worker

CleanScout 的 Ubuntu PC OpenClaw worker。

它不是 ROS 节点，也不是 OpenClaw Dashboard。它只做第一版对话链路：

```text
云端 backend <- WebSocket -> pc-openclaw-worker -> 本机 OpenClaw Gateway
```

## 运行前检查

```bash
cd tools/pc-openclaw-worker
cp .env.example .env
npm ci
npm run probe
```

`probe` 只检查本机 `OpenClaw Gateway`：

```text
GET  http://127.0.0.1:18789/v1/models
POST http://127.0.0.1:18789/v1/chat/completions
```

## 前台联调

```bash
npm run start
```

看到下面日志即表示云端鉴权已通过，worker 正在等待云端下发聊天请求：

```text
registered device=cleanscout-001 agent=pc-yusu-main
token accepted; websocket session is authenticated and waiting for requests
heartbeat sent ... waitingFor=OPENCLAW_CHAT_REQUEST
```

这不是卡住。worker 是常驻进程，注册成功后就应该一直等 `OPENCLAW_CHAT_REQUEST`。

## 后台运行

推荐用 systemd user service。把仓库里的 `pc-openclaw-worker.service.example` 复制到：

```text
~/.config/systemd/user/pc-openclaw-worker.service
```

然后按实际路径修改 `WorkingDirectory` 和 `EnvironmentFile`。

启动：

```bash
systemctl --user daemon-reload
systemctl --user enable --now pc-openclaw-worker.service
systemctl --user status pc-openclaw-worker.service --no-pager
```

看日志：

```bash
journalctl --user -u pc-openclaw-worker -f
```

如果希望 SSH 退出后仍保持 user service：

```bash
sudo loginctl enable-linger $USER
```

## Token 边界

`.env` 中有两个 token：

```text
CLOUD_AGENT_TOKEN=<云端 backend AGENT_SHARED_SECRET>
OPENCLAW_GATEWAY_TOKEN=<本机 OpenClaw Gateway token>
```

说明：

- `CLOUD_AGENT_TOKEN` 只在 worker 注册云端时校验。
- 注册通过后，同一个 WebSocket session 不会每条消息重复鉴权。
- 断线重连时会重新注册并重新校验 token。
- `OPENCLAW_GATEWAY_TOKEN` 只留在 Ubuntu PC 本机，不进云端 backend，不进前端。
