# CleanScout pc-camera-worker

UbuntuPC 侧 ESP32-CAM 图传转发工具。

职责固定为：

- 从手机热点内网拉取 ESP32-CAM MJPEG：`CAMERA_SOURCE_URL`
- 默认使用 `CAMERA_UPLINK_MODE=raw-mjpeg`，把 ESP32-CAM 原始 multipart 字节流直接隧道转发到云端
- 如需调试 snapshot 兜底，可切到 `CAMERA_UPLINK_MODE=jpeg-frame`，解析 JPEG 帧并按 `CAMERA_TARGET_FPS` 限流
- 主动连接云端 backend：`CAMERA_CLOUD_WS`
- 注册、心跳、推送 raw MJPEG chunk 或二进制 JPEG 帧

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
CAMERA_UPLINK_MODE=raw-mjpeg
CAMERA_TARGET_FPS=20
CAMERA_MAX_FRAME_BYTES=500000
CAMERA_MAX_CLOUD_BUFFERED_BYTES=2097152
CAMERA_CLOUD_WS=wss://api.hzhhds.top/edge/camera
CAMERA_CLOUD_TOKEN=<与 backend CAMERA_INGEST_TOKEN 相同>
```

`CAMERA_CLOUD_TOKEN` 只放在 UbuntuPC 本机 `.env`，不要提交。

`raw-mjpeg` 是正式展示模式：worker 不重编码、不拆帧限速，直接转发 ESP32-CAM `/stream` 的 multipart 输出。`jpeg-frame` 是兼容模式，主要用于 snapshot 兜底和 mock 验证。
