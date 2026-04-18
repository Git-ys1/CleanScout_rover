# V-1.6.0 第二次 ROS 本地联调记录

## 本轮目标

继续沿用已跑通的本地链路：

```text
uni-app 前端 -> backend local-lan profile -> rosbridge -> ROS
```

本轮不改拓扑，不做公网 ROS，不处理 NAT / FRP / VPN / ECS 穿透。

## 运行 profile

本次使用独立测试端口 `3100`，避免打断用户当前 `3000` 端口上的 backend。

启动参数：

```text
APP_PROFILE=local-lan
ENV_FILE=<临时 local-lan env file>
PORT=3100
ROS_TRANSPORT=rosbridge
ROSBRIDGE_URL=ws://10.117.77.84:9090
```

backend 启动日志已确认：

```text
[runtime] APP_PROFILE=local-lan
[runtime] ROS_TRANSPORT=rosbridge
[runtime] ROSBRIDGE_URL=ws://10.117.77.84:9090
[runtime] OPENCLAW_ENABLED=false
```

## 第一次实测：中途失败

`2026-04-18` 第一次复测时出现失败：

- `GET /api/system/health`：通过
- `GET /api/integrations/ros/status`：
  - `transport=rosbridge`
  - `connected=false`
  - `lastError=connect ETIMEDOUT 10.117.77.84:9090`
- `GET /api/ros/telemetry/summary`：
  - `odomAvailable=false`
  - `imuAvailable=false`
  - `scanAvailable=false`
- `POST /api/ros/manual-preset`：
  - 失败
  - 错误：`connect ETIMEDOUT 10.117.77.84:9090`

端口层复核：

```text
Test-NetConnection 10.117.77.84 -Port 9090
TCP connect failed
Ping timed out
```

原因复核：

- backend profile loader 行为正确
- backend 已按 `local-lan` 启动并读取 `ROS_TRANSPORT=rosbridge`
- 失败根因是本机中途脱离热点 / 局域网，导致到 `10.117.77.84` 无法连通

## 第二次实测：恢复热点后通过

恢复热点后再次验证：

- `Test-NetConnection 10.117.77.84 -Port 9090`
  - `TcpTestSucceeded=True`
- `GET /api/integrations/ros/status`
  - `transport=rosbridge`
  - `connected=true`
  - `rosbridgeUrl=ws://10.117.77.84:9090`
  - `lastError=`
- `GET /api/ros/telemetry/summary`
  - `odomAvailable=true`
  - `imuAvailable=true`
  - `scanAvailable=true`
  - `lastOdomAt`、`lastImuAt`、`lastScanAt` 均已更新
- `POST /api/ros/manual-preset`
  - `preset=stop`
  - `accepted=true`
  - `transport=rosbridge`

## 结论

本轮 ROS 第二次真联调最终通过。

本次暴露出的关键风险是：如果本机脱离热点或热点隔离，backend 会正确报 `connect ETIMEDOUT 10.117.77.84:9090`。这不是代码 profile 错误，也不是 rosbridge 参数 missing，而是网络链路断开。

## 后续现场确认项

1. 本机是否仍保持 `10.117.77.190`
2. 树莓派是否仍保持 `10.117.77.84`
3. 本机和树莓派是否仍在同一热点 / 局域网
4. 若再次超时，先查端口层：

```powershell
Test-NetConnection 10.117.77.84 -Port 9090
```
