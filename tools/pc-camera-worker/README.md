# CleanScout pc-camera-worker

UbuntuPC 侧 ESP32-CAM 图传转发工具。

职责固定为：

1. 从手机热点内网拉取 ESP32-CAM MJPEG：`CAMERA_SOURCE_URL`
2. 解析 JPEG 帧并按 `CAMERA_TARGET_FPS` 限流
3. 主动连接云端 backend：`CAMERA_CLOUD_WS`
4. 注册、心跳、推送二进制 JPEG 帧

## 启动

```bash
cd tools/pc-camera-worker
npm install
cp .env.local .env
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
CAMERA_FRAMESIZE=7
CAMERA_HMIRROR=1
CAMERA_VFLIP=1
CAMERA_TARGET_FPS=8
CAMERA_CLOUD_WS=wss://api.hzhhds.top/edge/camera
CAMERA_CLOUD_TOKEN=<与 backend CAMERA_INGEST_TOKEN 相同>
```

`CAMERA_CLOUD_TOKEN` 只放在 UbuntuPC 本机 `.env`，不要提交。

如果只是先拷一份本地运行模板，优先使用：

```bash
cp .env.local .env
```

## 后台运行

快速后台运行：

```bash
bash ./run-background.sh
```

查看状态：

```bash
bash ./status-background.sh
```

停止：

```bash
bash ./stop-background.sh
```

日志默认写到：

```text
tools/pc-camera-worker/.runtime/pc-camera-worker.log
```

如果希望开机后用户登录即自动拉起，可使用：

```bash
mkdir -p ~/.config/systemd/user
cp ./pc-camera-worker.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now pc-camera-worker.service
```

## 目录

```text
tools/pc-camera-worker/
  package.json
  .env.example
  src/
    index.js
    config.js
    cloudCameraClient.js
    esp32camClient.js
    mjpegParser.js
    diagnostics.js
```

## 当前定位

1. 不属于 Raspberry Pi edge-relay 主职责
2. 不直接做 ROS 节点
3. 只负责 UbuntuPC 本机图传接入与云端上送

## 联调观察

当前现场联调结论：

1. ESP32-CAM 直连本地网页时，主观流畅度高于经过 `pc-camera-worker -> backend -> H5` 的链路。
2. 当前 UbuntuPC worker 实测稳定上送帧率通常在 `10~11 FPS` 左右，不会简单等于 `CAMERA_TARGET_FPS`。
3. 摄像头源头分辨率档位对体验影响很大；当前联调建议优先使用较轻量的中档位，例如 `CAMERA_FRAMESIZE=7`，避免高分辨率下整链卡顿。
4. 若后端/H5 侧主观体验仍明显低于本地直连流，请后端侧同步核查：
   - `/edge/camera` 接收与最新帧缓存策略
   - `/api/integrations/openmv/stream` 输出刷新节奏
   - H5 `<img>` MJPEG 展示链的浏览器端表现
