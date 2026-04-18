---
version: V-1.4.0
based_on_branch: main
branch_source: GitHub branches page + origin/main fetch verification
published_to_root: vue3/
published_at_commit: d33b0c457935a106400c43845001579d0ad28a90
---

# V-1.4.0 前端打包脚本冻结 + 后端部署硬化 + ROS 联调合同

## 本轮结论

`V-1.4.0` 不改业务主线，只补上线前必须冻结的三类基础设施：

- 前端本地构建脚本
- backend 部署与 CORS 白名单
- ROS 联调合同文档

本轮仍然按新纪律执行：

- 先在 V 线自测分支冻结
- 再把 `vue3/` supplement merge 到 `main`
- 不覆盖 `Raspberrypi/` 和其他 C 线目录

## 本轮新增内容

### V-1.4.1 前端打包脚本

- `scripts/release-mp-weixin.ps1`
- `scripts/release-mp-weixin.sh`
- `scripts/release-app-plus.ps1`
- `docs/releases/V-1.4.0/mini-program-build.md`

当前规则：

- 微信小程序构建直接复用现有 `npm run build:mp-weixin`
- 构建完成后固定输出 `dist/build/mp-weixin`
- `release-app-plus.ps1` 是明确的占位脚本，不伪装成已可构建

### V-1.4.2 backend 部署硬化

- `backend/src/app.js` 已切到 `CORS_ALLOWED_ORIGINS` 白名单
- `backend/.env.example` 已补 `CORS_ALLOWED_ORIGINS`
- `backend/package.json` 已补 `prisma:migrate:deploy`
- `deploy/systemd/vline-backend.service`
- `scripts/deploy-backend.sh`
- `scripts/update-backend.sh`
- `docs/releases/V-1.4.0/backend-deploy.md`

当前部署结论：

- 生产环境默认按 Linux + systemd 单机 VPS 冻结
- 当前 `SQLite` 只适合单机 / 小流量阶段
- 生产 `DATABASE_URL` 必须放到 repo 工作树外部

### V-1.4.3 ROS 联调合同

- `docs/releases/V-1.4.0/ros-integration-contract.md`

合同冻结内容：

- backend 当前依赖的 ROS 环境变量
- 默认 rosbridge 端口 `9090`
- 期待 topic：`/cmd_vel`、`/odom`、`/imu/data`、`/scan`
- 如果 backend 在公网而树莓派在热点 / NAT 内，必须额外提供隧道、VPN 或反向桥

## 验证

已完成：

- `scripts/release-mp-weixin.ps1` 实测可调用 `build:mp-weixin`
- 微信小程序构建完成后可输出 `dist/build/mp-weixin`
- `scripts/release-app-plus.ps1` 会明确失败并提示“当前只是占位”
- `bash -n` 已检查：
  - `scripts/release-mp-weixin.sh`
  - `scripts/deploy-backend.sh`
  - `scripts/update-backend.sh`
- backend CORS 白名单已实测：
  - 无 `Origin` 请求：`200`
  - 白名单域名：`200`
  - 非白名单域名：`403`

## 未完成项

本轮明确未做：

- `build:app-plus` 真正落地
- `APK / IPA` 云打包流程
- PostgreSQL 迁移
- 容器化部署
- 真实树莓派 ROS 实机联调

这些内容继续留给后续发布轮单独冻结。
