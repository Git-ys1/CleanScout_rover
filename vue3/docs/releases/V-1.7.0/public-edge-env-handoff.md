# V-1.7.10 public-edge 云端 env 交付说明

## 本轮结论

云端 backend 使用 `public-edge` profile。

正式链路：

```text
小程序 / App / H5 -> https://api.hzhhds.top/api
edge-relay(Pi) -> wss://api.hzhhds.top/edge/ros
```

## /etc/vline-backend.env 口径

云端 `/etc/vline-backend.env` 必须使用 `public-edge`，核心字段为：

```text
APP_PROFILE=public-edge
PORT=3000
DATABASE_URL="file:/var/lib/vline-backend/dev.db"
JWT_SECRET="<生产 JWT secret，至少 32 位随机字符串>"
JWT_EXPIRES_IN=7d
CORS_ALLOWED_ORIGINS=https://h5.hzhhds.top,https://admin.hzhhds.top,https://cleanscoutrover-management.netlify.app

OPENCLAW_ENABLED=false
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_API_MODE=chat
OPENCLAW_MODEL=openclaw/default
OPENCLAW_BEARER_TOKEN=
OPENCLAW_REQUEST_TIMEOUT_MS=30000

ROS_ENABLED=true
ROS_TRANSPORT=edge-relay
ROSBRIDGE_URL=ws://127.0.0.1:9090
ROS_CMD_VEL_TOPIC=/cmd_vel
ROS_ODOM_TOPIC=/odom
ROS_IMU_TOPIC=/imu/data
ROS_SCAN_TOPIC=/scan
ROS_CMD_REPEAT_HZ=10
ROS_CMD_DEFAULT_HOLD_MS=400
ROS_RECONNECT_DELAY_MS=1000

EDGE_RELAY_ENABLED=true
EDGE_RELAY_PATH=/edge/ros
EDGE_DEVICE_AUTH_REQUIRED=true
EDGE_HELLO_TIMEOUT_MS=5000
EDGE_HEARTBEAT_TIMEOUT_MS=15000
EDGE_SERVER_PING_INTERVAL_MS=25000
EDGE_ALLOWED_DEVICE_IDS=csrpi-001
EDGE_DEVICE_BOOTSTRAP_ID=csrpi-001
EDGE_DEVICE_BOOTSTRAP_TOKEN="<生产 edge device token，至少 32 位随机字符串>"
```

## H5 / 第三方托管 CORS 规则

`CORS_ALLOWED_ORIGINS` 只管浏览器 H5 / admin web 的 `Origin` 校验，不管微信小程序合法域名。

当前 H5 已绑定自定义域名：

```text
https://h5.hzhhds.top
```

如果 H5 同时允许从第三方托管平台默认域名访问，例如 Netlify 默认域名：

```text
https://cleanscoutrover-management.netlify.app
```

则 VPS 的 `/etc/vline-backend.env` 必须把该 Origin 一并写入：

```text
CORS_ALLOWED_ORIGINS=https://h5.hzhhds.top,https://admin.hzhhds.top,https://cleanscoutrover-management.netlify.app
```

修改后必须重启 backend：

```bash
sudo systemctl restart vline-backend
```

如果只允许正式自定义域名访问，可以不加入 Netlify 默认域名；但此时从 `https://cleanscoutrover-management.netlify.app` 打开 H5，请求 backend 会被 CORS 拦截。

## 关于 loopback 地址

`public-edge` 下保留两个 loopback 地址是有意设计：

- `OPENCLAW_BASE_URL=http://127.0.0.1:18789`：当前 `OPENCLAW_ENABLED=false`，不会实际调用；后续若 OpenClaw Gateway 也部署在同一台云端机器或通过隧道映射到本机，再启用。
- `ROSBRIDGE_URL=ws://127.0.0.1:9090`：当前 `ROS_TRANSPORT=edge-relay`，不会走 rosbridge；该字段只作为兼容配置保留。

云端真实 ROS 链路只看：

```text
ROS_TRANSPORT=edge-relay
EDGE_RELAY_ENABLED=true
EDGE_RELAY_PATH=/edge/ros
```

## seed 规则

首次部署后，必须在云端执行：

```bash
cd /opt/vline-backend/backend
npx prisma generate
npx prisma migrate deploy
npx prisma db seed
```

`EDGE_DEVICE_BOOTSTRAP_TOKEN` 只在 seed 时使用。入库后保存的是 bcrypt hash，不是明文。

如果后续要更换 token，需要重新更新 `EdgeDevice(csrpi-001).tokenHash`，不能只改 env 后不处理数据库。

## C 线回传内容

给 Pi / edge-relay 的公网三项是：

```text
deviceId=csrpi-001
token=<EDGE_DEVICE_BOOTSTRAP_TOKEN 的明文值>
wsUrl=wss://api.hzhhds.top/edge/ros
```

本地联调 token 不复用到公网。公网必须使用生产 token。

## 微信小程序配置

微信小程序后台需要配置：

```text
request 合法域名：https://api.hzhhds.top
```

如果小程序未来直接使用 WebSocket，再另行配置：

```text
socket 合法域名：wss://api.hzhhds.top
```

当前小程序前端不直连 `/edge/ros`，因此本轮不要求小程序 socket 合法域名。
