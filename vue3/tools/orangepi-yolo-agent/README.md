# Orange Pi YOLO Agent

正式链路：

```text
原聊天页 -> cloud backend -> wss://api.hzhhds.top/ws/agents
        -> Orange Pi Agent -> Agnes + 最新 YOLO JPEG -> cloud backend -> 原聊天页
```

部署目标固定为 `/home/orangepi/Agent`。将本目录文件、`agent.py` 和包含 Agnes
配置的 `.env` 放到该目录，然后：

```bash
cd /home/orangepi/Agent
cp .cloud-agent.json.example .cloud-agent.json
printf '%s' '<与 VPS AGENT_SHARED_SECRET 相同的 token>' > .cloud-agent-token
chmod 600 .env .cloud-agent-token .cloud-agent.json
chmod 700 setup.sh start_cloud_agent.sh stop_cloud_agent.sh
./setup.sh
./start_cloud_agent.sh
```

查看日志：

```bash
tail -f /home/orangepi/Agent/logs/cloud-agent.log
```

Worker 只读取 `~/rk3588_ai/debug_logs/**/latest_debug.jpg`，不发送机械臂指令。
超过 `max_frame_age_seconds` 的图片不会作为实时截图返回。
