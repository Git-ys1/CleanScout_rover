---
version: V-1.5.6
based_on_branch: main
branch_source: GitHub branches page + origin/main latest branch policy
published_to_root: vue3/
published_at_commit: 919cb3ff1fcba194ceae46acebef4f02e2b25f25
---

# V-1.5.6 backend 本机 ROS 环境漂移热修

## 本轮结论

`2026-04-18 21:11` 复查时，树莓派 `rosbridge` 本身是通的，端口 `10.117.77.84:9090` 可达。

当时前端看到 ROS 参数 missing / 未接入，根因不是 ROS 未启动，而是本机正在运行的 backend 仍读取旧 `backend/.env`：

```text
PORT=3000
DATABASE_URL="file:./dev.db"
JWT_SECRET="v-line-local-dev-secret"
JWT_EXPIRES_IN=7d
```

这份旧本地环境文件没有任何 `ROS_*` 配置，所以 backend 会按代码默认值退回：

```text
ROS_TRANSPORT=mock
ROSBRIDGE_URL=ws://127.0.0.1:9090
```

## 已执行热修

已将本机 `backend/.env` 改成本地联调口径。

说明：

- `backend/.env` 是本机运行文件，不入 Git
- 仓库内正式模板仍是 `deploy/env/vline-backend.local-lan.env.example`
- 后续换机器或重部署时，必须从模板同步到实际环境文件

关键项如下：

```text
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
ROS_ENABLED=true
ROS_TRANSPORT=rosbridge
ROSBRIDGE_URL=ws://10.117.77.84:9090
ROS_CMD_VEL_TOPIC=/cmd_vel
ROS_ODOM_TOPIC=/odom
ROS_IMU_TOPIC=/imu/data
ROS_SCAN_TOPIC=/scan
ROS_CMD_REPEAT_HZ=10
ROS_CMD_DEFAULT_HOLD_MS=400
ROS_RECONNECT_DELAY_MS=1000
```

## 本机复测结果

热修后已重启本机 backend，并完成接口复测：

- `GET /api/integrations/ros/status`
  - `transport=rosbridge`
  - `connected=true`
  - `rosbridgeUrl=ws://10.117.77.84:9090`
- `GET /api/ros/telemetry/summary`
  - `odomAvailable=true`
  - `imuAvailable=true`
  - `scanAvailable=true`
  - `lastOdomAt`、`lastImuAt`、`lastScanAt` 均已更新
- `POST /api/ros/manual-preset`
  - `preset=stop`
  - `accepted=true`
  - `transport=rosbridge`

## 后续纪律

以后如果前端显示 ROS 参数 missing，先查三件事：

1. 当前 backend 进程读取的实际环境文件
2. `GET /api/integrations/ros/status` 返回的 `transport`
3. `ROSBRIDGE_URL` 是否仍是 `ws://10.117.77.84:9090`

不能只看仓库模板；模板正确不代表当前运行进程已经加载了正确环境。
