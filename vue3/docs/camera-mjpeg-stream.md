# V-2.2.0 ESP32-CAM MJPEG 云端图传说明

## 结论

本轮图传主链路不再使用单帧周期刷新，而是使用 UbuntuPC 主动上送 MJPEG 帧：

```text
ESP32-CAM
  -> UbuntuPC pc-camera-worker
  -> wss://api.hzhhds.top/edge/camera
  -> backend 最新帧缓存
  -> https://api.hzhhds.top/api/integrations/openmv/stream
  -> H5 前视画面
```

前端不直连 ESP32-CAM，云端 backend 也不主动访问手机热点内网 IP。

## 组件职责

- `ESP32-CAM`：独立 STA 摄像头，连接手机热点并输出 HTTP/MJPEG。
- `UbuntuPC camera-worker`：拉取 ESP32-CAM MJPEG，解析 JPEG 帧，限帧率后推送云端。
- `backend`：鉴权接收 `/edge/camera`，只缓存最新帧，向前端输出 `/stream`。
- `H5 前端`：使用 `<img>` 显示 MJPEG stream；小程序 / App 保留 snapshot 兜底。

## backend env

```text
OPENMV_ENABLED=true
OPENMV_INPUT_MODE=push-stream

CAMERA_INGEST_ENABLED=true
CAMERA_INGEST_PATH=/edge/camera
CAMERA_INGEST_TOKEN=<与 UbuntuPC CAMERA_CLOUD_TOKEN 相同>
CAMERA_ALLOWED_DEVICE_IDS=pc-001
CAMERA_ALLOWED_CAMERA_IDS=openmv-arm-cam-001
CAMERA_FRAME_STALE_MS=3000
CAMERA_MAX_FRAME_BYTES=300000
CAMERA_STREAM_BOUNDARY=cleanscout-openmv
CAMERA_STREAM_HEARTBEAT_MS=1000
CAMERA_MAX_VIEWERS=3
```

`CAMERA_INGEST_TOKEN` 只进部署 env，不写入仓库。

## UbuntuPC worker env

```text
DEVICE_ID=pc-001
CAMERA_ID=openmv-arm-cam-001
CAMERA_SOURCE_URL=http://ESP32-CAM-IP:81/stream
CAMERA_TARGET_FPS=8
CAMERA_MAX_FRAME_BYTES=200000
CAMERA_CLOUD_WS=wss://api.hzhhds.top/edge/camera
CAMERA_CLOUD_TOKEN=<与 backend CAMERA_INGEST_TOKEN 相同>
```

启动：

```bash
cd vue3/tools/pc-camera-worker
npm install
cp .env.example .env
nano .env
npm run start
```

无真实摄像头时可以先跑 mock：

```bash
npm run mock
```

## backend 接口

- `GET /api/integrations/openmv/status`
- `GET /api/integrations/openmv/stream?token=<JWT>`
- `GET /api/integrations/openmv/snapshot?token=<JWT>`

`/stream` 与 `/snapshot` 使用登录 JWT query token，因为 `<img>` 无法携带 `Authorization` header。

## Nginx

云端需要同时反代：

- `/edge/camera`：WebSocket，显式透传 `Upgrade` / `Connection`
- `/api/integrations/openmv/stream`：关闭 `proxy_buffering`，避免 MJPEG 被缓冲

仓库模板见：

```text
deploy/nginx/api.hzhhds.top.conf
```

## 常见故障

- `status.cameraOnline=false`：worker 未连接、无新帧，或超过 `CAMERA_FRAME_STALE_MS`。
- `CAMERA_TOKEN_INVALID`：UbuntuPC `CAMERA_CLOUD_TOKEN` 与云端 `CAMERA_INGEST_TOKEN` 不一致。
- 前端显示离线：先查 `/api/integrations/openmv/status`，再查 worker 日志。
- H5 能看、小程序不连续：小程序端保留 snapshot 兜底，本轮以 H5 MJPEG 为正式展示端。

## Raspberry Pi 边界

ESP32-CAM 图传不属于 Raspberry Pi edge-relay 主职责。Raspberry Pi 继续负责 ROS 移动、感知、继电器 / 风机 edge-relay；图传由 UbuntuPC camera-worker 负责。
