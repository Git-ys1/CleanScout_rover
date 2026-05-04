# V 线 vue3 部署与联调统一文档

## 文档纪律

从 `V-1.8.9` 起，`vue3/` 的部署、构建、本地联调、云端联调与运维口径统一收敛到本文档。

后续不要再为部署流程新建分散文档；历史 `docs/releases/*` 只作为历史快照保留，不再作为当前操作入口。

## 凭据纪律

以下凭据不得明文提交到云端仓库：

- `EDGE_DEVICE_BOOTSTRAP_TOKEN`
- `edge_device_token`
- `OPENCLAW_BEARER_TOKEN`
- `JWT_SECRET`

当前只在本文档记录字段名、用途、存放位置和交接方式。需要复制明文时，到对应运行环境读取：

- 本地 edge-relay：树莓派启动命令里的 `edge_device_token`，以及本机 backend 使用的临时 env / SQLite seed 状态。
- 云端 edge-relay：VPS `/etc/vline-backend.env` 里的 `EDGE_DEVICE_BOOTSTRAP_TOKEN`，seed 后数据库只保存 bcrypt hash。
- OpenClaw：树莓派 OpenClaw handoff 文档里的 `OPENCLAW_BEARER_TOKEN`，VPS 或本地 backend env 中只写 `OPENCLAW_BEARER_TOKEN`。

当前固定设备标识：

```text
edge_device_id=csrpi-001
EDGE_DEVICE_BOOTSTRAP_ID=csrpi-001
```

## 树莓派侧准备

### 启动 pigpiod

```bash
sudo pigpiod
```

判断是否启动成功：

```bash
pgrep -a pigpiod
```

预期输出带有进程号即可，例如：

```text
65477 pigpiod
```

### 编译 ROS 工作区

```bash
cd /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
catkin_make
```

### 启动多功能节点

该节点覆盖：

- 底盘遥控
- 风机继电器 / 舵机开关
- 双风机 PWM
- 风机转速回传

启动：

```bash
cd /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
source ./use_cleanscout_pi.sh
roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/demo/multi_function_demo.launch \
  enable_edge_relay:=true \
  edge_device_id:=csrpi-001 \
  edge_device_token:=<EDGE_DEVICE_TOKEN 明文，仅现场联调用，不入仓> \
  edge_url:=ws://<backend所在机器IP>:3000/edge/ros
```

本地热点联调时，`edge_url` 示例：

```text
ws://10.156.250.190:3000/edge/ros
```

本机 IP 会随热点 / WiFi 变化，必须以当前 `ipconfig` 或本地启动脚本输出为准。

## 本地 H5 / edge-relay 联调

### 推荐一条命令启动

在仓库根目录执行：

```powershell
cd F:\Project\CSc——uniapp\vue3
cmd /c npm.cmd run local:edge
```

该命令会：

1. 生成本地 `public-edge` 临时 env 文件。
2. 新开窗口启动 backend。
3. 新开窗口启动 H5 前端。
4. 打印当前局域网 `edge` 地址。

访问地址：

```text
H5: http://localhost:5173
backend: http://127.0.0.1:3000
edge: ws://<当前本机局域网IP>:3000/edge/ros
```

### 手动启动本地前端 H5

```powershell
cd F:\Project\CSc——uniapp\vue3
cmd /c npm.cmd run dev:h5
```

访问：

```text
http://localhost:5173
```

### 手动启动本地后端

```powershell
cd F:\Project\CSc——uniapp\vue3\backend
$env:ENV_FILE="$env:TEMP\vline-backend-public-edge-local.env"
cmd /c npm.cmd run start
```

树莓派 edge 联调参数：

```text
edge_url:=ws://<当前本机局域网IP>:3000/edge/ros
edge_device_id:=csrpi-001
edge_device_token:=<EDGE_DEVICE_TOKEN 明文，仅现场联调用，不入仓>
```

## 小程序 / App 构建

### 微信小程序生产构建

```powershell
cd /d F:\Project\CSc——uniapp\vue3
cmd /c npm.cmd run build:mp-weixin:production
```

产物目录：

```text
F:\Project\CSc——uniapp\vue3\dist\build\mp-weixin
```

微信开发者工具导入该目录。

### App 生产构建

```powershell
cd /d F:\Project\CSc——uniapp\vue3
cmd /c npm.cmd run build:app:production
```

产物目录：

```text
F:\Project\CSc——uniapp\vue3\dist\build\app
```

说明：uni-app CLI 侧生成 App 资源；真正 APK / IPA 打包仍按后续 HBuilderX / 云打包流程处理。

## 云端后端 VPS：当前主用 ljdVPS

当前云端 backend 采用 `public-edge` profile。

显示域名：

```text
api.hzhhds.top
```

VPS 信息：

```text
供应方：ljd aliyun
公网 IP：47.86.13.211
实例名称：CleanScout_rover_vue3backend_2
```

### 首次部署

如果需要网络代理，先安装并配置代理服务。

拉取云端仓库：

```bash
sudo mkdir -p /opt/cleanscout-src
cd /opt/cleanscout-src
sudo git clone https://github.com/Git-ys1/CleanScout_rover.git .
```

创建 `/etc/vline-backend.env`，按 `deploy/env/vline-backend.public-edge.env.example` 填写真实生产值。

部署：

```bash
cd /opt/cleanscout-src/vue3
sudo bash scripts/bootstrap-backend.sh
```

部署后验收：

```bash
cd /opt/cleanscout-src/vue3
sudo bash scripts/check-backend-state.sh
```

验收不通过时，不允许继续宣称云端 backend 可用。

### 后续更新

```bash
cd /opt/cleanscout-src/vue3
sudo bash scripts/update-backend.sh
```

如果已配置 shell alias，也可使用：

```bash
update-backend
```

### public-edge env 关键项

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
OPENCLAW_BEARER_TOKEN=<OpenClaw token，仅启用 OpenClaw 时填写，不入仓>
OPENCLAW_REQUEST_TIMEOUT_MS=30000

ROS_ENABLED=true
ROS_TRANSPORT=edge-relay
ROSBRIDGE_URL=ws://127.0.0.1:9090

EDGE_RELAY_ENABLED=true
EDGE_RELAY_PATH=/edge/ros
EDGE_DEVICE_AUTH_REQUIRED=true
EDGE_ALLOWED_DEVICE_IDS=csrpi-001
EDGE_DEVICE_BOOTSTRAP_ID=csrpi-001
EDGE_DEVICE_BOOTSTRAP_TOKEN=<生产 edge device token，至少 32 位随机字符串，不入仓>
```

说明：

- `OPENCLAW_ENABLED=false` 时，`OPENCLAW_BASE_URL` 和 `OPENCLAW_BEARER_TOKEN` 不参与运行。
- `ROS_TRANSPORT=edge-relay` 时，云端不走 `ROSBRIDGE_URL`，树莓派通过 `wss://api.hzhhds.top/edge/ros` 主动连接 backend。
- `CORS_ALLOWED_ORIGINS` 只给浏览器 H5 / admin web 使用；微信小程序合法域名在微信后台配置。
- H5 同时支持自定义域名和 Netlify 默认域名时，两个 Origin 都必须加入 CORS。

## 云端前端 H5：Netlify

当前 H5 前端托管在 Netlify。

访问域名：

```text
https://h5.hzhhds.top
https://cleanscoutrover-management.netlify.app
```

Netlify 项目：

```text
cleanscoutrover-management
```

构建口径：

```text
Build command: npm ci && npm run build:h5:production
Publish directory: dist/build/h5
```

如果 Netlify 的 base directory 配置为仓库根目录而不是 `vue3/`，则 publish directory 应对应调整为：

```text
vue3/dist/build/h5
```

当前生产 API：

```text
https://api.hzhhds.top/api
```

## 微信小程序云端调试

微信小程序后台配置：

```text
request 合法域名：https://api.hzhhds.top
```

当前小程序前端不直连 `/edge/ros`，因此本轮不要求配置 socket 合法域名。

如果未来小程序直接使用 WebSocket，再配置：

```text
socket 合法域名：wss://api.hzhhds.top
```

## 旧版 zlwVPS 记录

旧 VPS 只作为历史记录，不作为当前部署入口。

```text
供应方：zlw aliyun
公网 IP：121.89.87.242
实例名称：CleanScout_rover_vue3backend_1
域名：api.hzhhds.top
```

该机器曾使用手动 DNS-01 证书：

```text
fullchain: /etc/letsencrypt/live/api.hzhhds.top/fullchain.pem
privkey:   /etc/letsencrypt/live/api.hzhhds.top/privkey.pem
到期时间：2026-07-31
```

手动续期命令：

```bash
sudo certbot certonly --manual --preferred-challenges dns -d api.hzhhds.top
sudo nginx -t
sudo systemctl reload nginx
```

## 当前阶段结论

`V-1.8.9` 后，V 线部署口径为：

- 本地联调：`npm run local:edge`
- 小程序生产构建：`build:mp-weixin:production`
- App 构建：`build:app:production`
- 云端后端主用：ljdVPS `47.86.13.211`
- 云端 backend profile：`public-edge`
- 云端 H5：Netlify `h5.hzhhds.top`
- edge 设备：`csrpi-001`
- 明文 token 不写入仓库，按 env / handoff 文档 / 现场启动参数交接
