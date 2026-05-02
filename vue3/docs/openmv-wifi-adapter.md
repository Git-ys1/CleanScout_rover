# OpenMV WiFi 图传适配说明

## 当前结论

当前 V 线可以把 `OpenMV` 的前视图像接到现有前端里，但当前落地方式冻结为：

```text
前端 -> backend -> OpenMV WiFi 图传
```

不推荐前端长期直接连 `OpenMV` 图传地址。

原因：

- 现有 V 线主线已经冻结为“前端只找 backend”
- `OpenMV` 常见输出是 `MJPEG / HTTP` 或单帧快照，不适合直接塞进现有业务 API
- 通过 backend 代理后，前端只吃统一 `/api/integrations/openmv/*`
- 后续如果 `OpenMV` 改成别的 IP、别的路径、别的输出模式，只改 backend env，不改页面

## 官方依据

- WLAN 官方文档：`https://docs.openmv.io/library/network.WLAN.html`
- OpenMV WiFi MJPEG 示例：`https://book.openmv.cc/example/14-WiFi-Shield/mjpeg-streamer.html`

从官方文档可以确认两件事：

- `OpenMV` 支持 `STA` 和 `AP` 两种 WiFi 模式
- 官方已有基于 WiFi 的 `MJPEG` 图传示例

## 当前仓库已落地的接口

backend 新增：

- `GET /api/integrations/openmv/status`
- `GET /api/integrations/openmv/snapshot`

前端首页已新增：

- `OpenMV 前视画面` 卡片

当前前端显示方式不是直接吃完整视频播放器，而是：

- backend 从 `OpenMV` 拉一帧
- 前端按固定周期刷新单帧
- 形成“准实时”前视预览

这样做的原因是：

- `uni-app` 多端下先做单帧代理最稳
- 不需要先在当前轮里硬啃完整视频协议兼容
- 对小车前视监看已经够用

## backend 环境变量

当前已补齐以下 env：

```text
OPENMV_ENABLED=false
OPENMV_BASE_URL=http://192.168.4.1:8080
OPENMV_MODE=mjpeg
OPENMV_STREAM_PATH=/
OPENMV_SNAPSHOT_PATH=/snapshot
OPENMV_REQUEST_TIMEOUT_MS=5000
OPENMV_PREVIEW_REFRESH_MS=1200
```

说明：

- `OPENMV_ENABLED`
  - 是否启用 OpenMV 图传代理
- `OPENMV_BASE_URL`
  - OpenMV 图传根地址
- `OPENMV_MODE`
  - `mjpeg | snapshot`
- `OPENMV_STREAM_PATH`
  - `mjpeg` 模式下的路径
- `OPENMV_SNAPSHOT_PATH`
  - `snapshot` 模式下的路径
- `OPENMV_PREVIEW_REFRESH_MS`
  - 前端单帧刷新周期

## 当前推荐接法

### 本地联调

如果当前是本地笔记本调试，推荐：

1. 让运行 backend 的机器接入 `OpenMV` 的 WiFi
2. backend 通过 `OPENMV_BASE_URL` 去访问图传
3. 前端继续只找 backend

### 风险边界

如果你的手机 / 小程序终端直接连到 `OpenMV` 自己的热点，而 backend 不在同一网络里，那么：

- 前端可能能看到 `OpenMV`
- 但同时可能失去对 backend 的访问

所以这轮的正确做法仍然是：

- 优先让 backend 所在设备接入 `OpenMV` WiFi
- 前端继续通过 backend 看前视图像

## 当前不做的事

- 不在当前轮直接把 `OpenMV` 变成前端直连主链路
- 不在当前轮引入完整 RTSP 播放链
- 不在当前轮把 OpenMV 图传和 ROS / OpenClaw 语义层混成一套 transport

## 下一步使用方式

1. 在 backend env 中把 `OPENMV_ENABLED=true`
2. 按实际 OpenMV 图传地址填写 `OPENMV_BASE_URL`
3. 根据实际输出选择 `OPENMV_MODE=mjpeg` 或 `snapshot`
4. 重启 backend
5. 登录前端首页，观察 `OpenMV 前视画面` 卡片
