# CleanScout pc-camera-worker

UbuntuPC 侧 ESP32-CAM 图传转发工具。

职责固定为：

- 从手机热点内网拉取 ESP32-CAM MJPEG：`CAMERA_SOURCE_URL`
- 解析 JPEG 帧并按 `CAMERA_TARGET_FPS` 限流，默认 20fps
- 主动连接云端 backend：`CAMERA_CLOUD_WS`
- 注册、心跳、推送二进制 JPEG 帧

## 启动

```bash
cd vue3/tools/pc-camera-worker
npm install
cp .env.example .env
nano .env
npm run start
```

## Mock 验证

没有真实摄像头时，可以先验证云端链路：

```bash
npm run mock
```

## 必填配置

```text
DEVICE_ID=pc-001
CAMERA_ID=openmv-arm-cam-001
CAMERA_SOURCE_URL=http://ESP32-CAM-IP:81/stream
CAMERA_TARGET_FPS=20
CAMERA_MAX_FRAME_BYTES=500000
CAMERA_CLOUD_WS=wss://api.hzhhds.top/edge/camera
CAMERA_CLOUD_TOKEN=<与 backend CAMERA_INGEST_TOKEN 相同>
```

`CAMERA_CLOUD_TOKEN` 只放在 UbuntuPC 本机 `.env`，不要提交。
