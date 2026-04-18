---
version: V-1.5.0
based_on_branch: main
branch_source: GitHub branches page + origin/main latest branch policy
published_to_root: vue3/
published_at_commit: pending-cloud-publish
---

# V-1.5.0 环境驱动配置 + 本地 ROS 真联调 + 微信网络规则冻结

## 本轮结论

`V-1.5.0` 不继续修页面细节，而是把前后端配置口径和本地 ROS 真联调先做实：

- 前端 API 改成 `VITE_*` 环境驱动
- backend 环境模板拆成 `local-lan / public`
- 本机 backend 已实连 `ws://10.117.77.84:9090`
- 微信小程序本地调试与正式发布规则已拆开写清

## 本轮新增与调整

### V-1.5.1 前端环境化

- `src/api/config.js`
- `src/api/ws.js`
- `.env.h5.local`
- `.env.mp-weixin.local`
- `.env.production`

当前规则：

- 不再硬编码 `127.0.0.1:3000/api`
- `VITE_API_BASE_URL` 必填
- `VITE_WS_BASE_URL` 当前允许留空
- backend 尚无真实 `/ws` 服务，因此前端 WS 保持禁用占位
- `build:h5` 固定走 `.env.h5.local`
- `build:mp-weixin` 固定走 `.env.mp-weixin.local`
- 正式微信小程序发布改由 `build:mp-weixin:production` 承担

### V-1.5.2 backend 模板分离

- `deploy/env/vline-backend.local-lan.env.example`
- `deploy/env/vline-backend.public.env.example`
- `backend/.env.example`

当前规则：

- 本地联调用 `local-lan`
- 公网部署用 `public`
- `/etc/vline-backend.env` 仍不入仓
- 小程序地址不填进 `CORS_ALLOWED_ORIGINS`

### V-1.5.3 本地 ROS 真联调

- `docs/releases/V-1.5.0/ros-local-lan-test.md`

当前冻结结论：

- 本机局域网 IP：`10.117.77.190`
- 树莓派 rosbridge：`ws://10.117.77.84:9090`
- 已实测：
  - `transport=rosbridge`
  - `connected=true`
  - `odom / imu / scan` 时间戳已更新
  - 管理员低速预设命令返回成功

### V-1.5.4 微信小程序网络规则

- `docs/releases/V-1.5.0/wechat-mini-program-network.md`

当前规则：

- 本地调试可指向 `http://10.117.77.190:3000/api`
- 正式发布必须使用公网 `HTTPS` 域名
- 微信后台配置的是 `服务器域名`，不是 backend 的 `CORS_ALLOWED_ORIGINS`

## 验证

已完成：

- `cmd /c npm.cmd run build:h5`
- `cmd /c npm.cmd run build:mp-weixin`
- `.\scripts\release-mp-weixin.ps1`
- 本机 backend 使用 `rosbridge` 真链路联调
- `GET /api/integrations/ros/status`
- `GET /api/ros/telemetry/summary`
- `POST /api/ros/manual-preset`

## 未完成项

本轮明确未做：

- backend 真 `/ws` 服务
- 小程序公网正式发布链路
- 公网 backend 直连局域网树莓派
- NAT / FRP / VPN / ECS 穿透方案

这些内容继续留给后续发布轮单独冻结。
