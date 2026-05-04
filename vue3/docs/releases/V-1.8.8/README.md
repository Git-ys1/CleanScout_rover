# V-1.8.8 后端首次部署闭环与自动验收

## 本轮结论

本轮补齐后端首次部署闭环：

- 首次部署使用 `scripts/bootstrap-backend.sh`
- 部署后验收使用 `scripts/check-backend-state.sh`
- 后续更新继续使用 `scripts/update-backend.sh`

本轮不改变：

- `DATABASE_URL=file:/var/lib/vline-backend/dev.db`
- `public-edge` profile
- `EdgeDevice` token 机制
- `update-backend.sh` 只做更新的职责边界

## 首次部署

适用场景：

- 新 VPS / 新系统
- 已经拉取 `CleanScout_rover` 仓库
- 准备第一次安装并启动 `vline-backend`

执行：

```bash
cd /opt/cleanscout-src/vue3
sudo bash scripts/bootstrap-backend.sh
```

脚本会自动执行：

- 检查 `/etc/vline-backend.env`
- 检查并安装缺失的 `node / npm / npx / rsync / sqlite3 / systemctl`
- 创建缺失的 `vline` systemd 服务用户
- 同步 `backend/` 到 `/opt/vline-backend/backend`
- 执行 `npm ci`
- 执行 `npx prisma generate`
- 执行 `npx prisma migrate deploy`
- 执行 `npx prisma db seed`
- 安装或刷新 `vline-backend.service`
- 修正 `/var/lib/vline-backend` 的服务用户写权限
- 重启 `vline-backend`
- 调用 `scripts/check-backend-state.sh` 做验收

## /etc/vline-backend.env 必填项

首次 `public-edge` 部署至少需要：

```text
DATABASE_URL="file:/var/lib/vline-backend/dev.db"
JWT_SECRET="<至少 32 位随机字符串>"
EDGE_DEVICE_BOOTSTRAP_ID=csrpi-001
EDGE_DEVICE_BOOTSTRAP_TOKEN="<至少 32 位随机 token>"
```

`EDGE_DEVICE_BOOTSTRAP_TOKEN` 只在 seed 时使用。

数据库里保存的是 `bcrypt` hash，不保存明文 token。

## 部署后验收

任意部署后可执行：

```bash
cd /opt/cleanscout-src/vue3
sudo bash scripts/check-backend-state.sh
```

脚本检查：

- `systemctl is-active vline-backend`
- SQLite 关键表：`User`、`SystemConfig`、`EdgeDevice`
- `admin` 用户是否存在且启用
- `system` 配置是否存在
- `csrpi-001` 设备是否存在且启用

如果发现数据库表或关键 seed 缺失，脚本会尝试执行：

```bash
npx prisma migrate deploy
npx prisma db seed
```

修复后仍失败，脚本会明确输出失败点。

## 后续更新

后续更新继续使用：

```bash
cd /opt/cleanscout-src/vue3
sudo bash scripts/update-backend.sh
```

更新脚本职责保持为：

- 同步最新 `backend/`
- 执行 `npm ci`
- 执行 `npx prisma generate`
- 执行 `npx prisma migrate deploy`
- 重启 `vline-backend`

更新脚本通常不重复 seed，避免后续更新误触设备 token 初始化状态。

## 全新机器推荐流程

```bash
sudo apt-get update
sudo apt-get install -y git

sudo mkdir -p /opt/cleanscout-src
cd /opt/cleanscout-src
git clone https://github.com/Git-ys1/CleanScout_rover.git .

sudo tee /etc/vline-backend.env >/dev/null <<'EOF'
APP_PROFILE=public-edge
PORT=3000
DATABASE_URL="file:/var/lib/vline-backend/dev.db"
JWT_SECRET="<至少 32 位随机字符串>"
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
EDGE_DEVICE_BOOTSTRAP_TOKEN="<至少 32 位随机 token>"
EOF

如果 H5 部署在 Netlify 等第三方平台，`CORS_ALLOWED_ORIGINS` 需要同时包含正式自定义域名和第三方默认域名。当前 Netlify 默认域名为：

```text
https://cleanscoutrover-management.netlify.app
```

否则从 Netlify 默认域名打开 H5 时，浏览器会被 backend CORS 拦截。微信小程序不使用这个字段，仍然在微信后台配置 `request 合法域名`。

cd /opt/cleanscout-src/vue3
sudo bash scripts/bootstrap-backend.sh
```

## 当前限制

- 自动安装依赖只支持 Ubuntu / Debian 的 `apt-get`
- 本轮不把 `git clone / git pull` 纳入 bootstrap，源码管理仍由运维显式执行
- 更换 `EdgeDevice` token 仍需单独运维处理，不靠更新脚本自动覆盖
