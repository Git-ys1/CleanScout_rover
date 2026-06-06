# CleanScout pc-camera-worker

UbuntuPC 侧 ESP32-CAM 图传转发工具。

职责固定为：

1. 从手机热点内网拉取 ESP32-CAM MJPEG：`CAMERA_SOURCE_URL`
2. 默认使用 `CAMERA_UPLINK_MODE=raw-mjpeg`，把 ESP32-CAM 原始 multipart 字节流直接隧道转发到云端
3. 如需调试 snapshot 兜底，可切到 `CAMERA_UPLINK_MODE=jpeg-frame`，解析 JPEG 帧并按 `CAMERA_TARGET_FPS` 限流
4. 主动连接云端 backend：`CAMERA_CLOUD_WS`
5. 注册、心跳、推送 raw MJPEG chunk 或二进制 JPEG 帧

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
CAMERA_SOURCE_URL=
CAMERA_SOURCE_HOST_SUFFIX=91
CAMERA_SOURCE_PORT=81
CAMERA_SOURCE_PATH=/stream
CAMERA_UPLINK_MODE=raw-mjpeg
CAMERA_FRAMESIZE=7
CAMERA_HMIRROR=1
CAMERA_VFLIP=1
CAMERA_TARGET_FPS=20
CAMERA_MAX_FRAME_BYTES=500000
CAMERA_MAX_CLOUD_BUFFERED_BYTES=2097152
CAMERA_CLOUD_WS=wss://api.hzhhds.top/edge/camera
CAMERA_CLOUD_TOKEN=<与 backend CAMERA_INGEST_TOKEN 相同>
```

`CAMERA_CLOUD_TOKEN` 只放在 UbuntuPC 本机 `.env`，不要提交。

若手机热点导致内网前三段变化，推荐不要写死 `CAMERA_SOURCE_URL`，而是让 worker 按当前 UbuntuPC IPv4 自动拼接固定主机号。当前默认 ESP32-CAM 固定主机号为 `91`。

`raw-mjpeg` 是正式展示模式：worker 不重编码、不拆帧限速，直接转发 ESP32-CAM `/stream` 的 multipart 输出。`jpeg-frame` 是兼容模式，主要用于 snapshot 兜底和 mock 验证。

## 热点地址约定

当前项目现场联调时，UbuntuPC、Raspberry Pi、ESP32-CAM 都连接到同一个手机热点。
这类场景下，**热点分配的内网前三段经常变化**，但某些设备在同一手机热点下的**主机号往往比较稳定**。

当前这套约定，是基于 **iQOO Z9 Turbo+** 热点下多轮联调观察得到的：

1. UbuntuPC：主机号常见为 `108`
2. Raspberry Pi：主机号常见为 `84`
3. ESP32-CAM：主机号常见为 `91`
4. 本地 fallback / relay 辅助主机：常按 `190` 处理

例如当前某一轮热点网段是：

```text
10.93.190.x
```

则现场设备常对应为：

```text
UbuntuPC   -> 10.93.190.108
RaspberryPi -> 10.93.190.84
ESP32-CAM  -> 10.93.190.91
fallback   -> 10.93.190.190
```

但这件事必须说明清楚：

1. 这些主机号是基于 **iQOO Z9 Turbo+** 热点环境观察到的结果
2. 不同手机热点、不同 DHCP 分配策略下，**固定主机号可能不同**
3. 因此这里的 `.84`、`.91`、`.108`、`.190` 不是通用网络标准，而是当前现场设备编排约定

当前建议：

1. UbuntuPC 的 ROS 环境脚本按当前网段自动推导 Raspberry Pi `.84`
2. `pc-camera-worker` 默认按当前网段自动推导 ESP32-CAM `.91`
3. 若后续更换手机热点后发现主机号不再稳定，应优先更新 `*_HOST_SUFFIX` 一类配置，而不是继续写死完整 IP

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
