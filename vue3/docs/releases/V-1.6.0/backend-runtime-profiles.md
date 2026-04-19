# V-1.6.0 backend runtime profile

## 新增运行参数

backend 从本轮开始支持：

```text
APP_PROFILE=local-lan
APP_PROFILE=public-cloud
ENV_FILE=/etc/vline-backend.env
```

启动顺序：

1. 按 `APP_PROFILE` 加载仓库模板默认值
2. 若设置 `ENV_FILE`，再加载指定环境文件并覆盖模板值
3. 若未设置 `ENV_FILE`，则尝试加载 `backend/.env` 并覆盖模板值

## local-lan

用途：

- 本地 H5 联调
- 微信小程序本地调试
- 本机 backend 连接局域网树莓派 `rosbridge`

关键值：

```text
APP_PROFILE=local-lan
ROS_TRANSPORT=rosbridge
ROSBRIDGE_URL=ws://10.117.77.84:9090
```

## public-cloud

用途：

- ECS / VPS 公网部署
- `api.hzhhds.top` 反代到本机 backend

关键值：

```text
APP_PROFILE=public-cloud
CORS_ALLOWED_ORIGINS=https://h5.hzhhds.top,https://admin.hzhhds.top
ROS_TRANSPORT=mock
```

公网版本轮不直连局域网树莓派；后续如果要公网控制，需要单独补 NAT / 隧道 / VPN / edge relay。

## 启动日志要求

backend 启动时必须打印：

- `APP_PROFILE`
- `profile_template`
- `ENV_FILE`
- `ROS_TRANSPORT`
- `ROSBRIDGE_URL`
- `OPENCLAW_ENABLED`

这用于避免再次出现“模板正确但进程实际读取旧 `.env`”的漂移。
