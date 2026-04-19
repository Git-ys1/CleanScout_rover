---
version: V-1.6.0
based_on_branch: main
branch_source: GitHub branches page + origin/main latest branch policy
published_to_root: vue3/
published_at_commit: 35f2bb383ae8156510b5cc1e266cd2dd71b55c17
---

# V-1.6.0 runtime profile 收口 + 第二次 ROS 真联调 + public-cloud 交付包 + edge-relay RFC

## 本轮结论

本轮完成四类收口：

- main 代码 / 文档漂移回归确认
- 前端 local / production profile 拆分
- backend `local-lan / public-cloud` runtime profile loader
- 第二次 ROS 本地真联调与 public-cloud 交付文档

同时新增 `edge-relay` RFC，但不替换当前已跑通的 `rosbridge` 链路。

## 关键新增

- `docs/releases/V-1.6.0/code-drift-check.md`
- `docs/releases/V-1.6.0/frontend-build-profiles.md`
- `docs/releases/V-1.6.0/backend-runtime-profiles.md`
- `docs/releases/V-1.6.0/ros-second-local-test.md`
- `docs/releases/V-1.6.0/public-cloud-deploy.md`
- `docs/releases/V-1.6.0/backend-centric-ros-relay-rfc.md`

## 验证结论

已完成：

- `src/api/config.js` 不再硬编码 `127.0.0.1:3000/api`
- backend 启动日志可打印 `APP_PROFILE / ENV_FILE / ROS_TRANSPORT / ROSBRIDGE_URL / OPENCLAW_ENABLED`
- `local-lan` profile 下第二次 ROS 联调最终通过
- `Test-NetConnection 10.117.77.84 -Port 9090` 恢复后通过
- `GET /api/integrations/ros/status` 返回 `transport=rosbridge`、`connected=true`
- `GET /api/ros/telemetry/summary` 返回 `odom / imu / scan` 可用
- `POST /api/ros/manual-preset` 的 `stop` 命令返回 `accepted=true`

## 未完成项

本轮明确未做：

- 实际登录 VPS 部署
- backend 真 `/ws` 服务
- 公网 backend 直连树莓派
- `edge-relay` 实现

## 后续评审项

`edge-relay` RFC 需 C 线负责人评审后才能进入施工轮。当前正式控制链路仍是：

```text
frontend -> backend -> rosbridge -> ROS
```
