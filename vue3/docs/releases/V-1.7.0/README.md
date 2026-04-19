---
version: V-1.7.0
based_on_branch: main
branch_source: GitHub branches page + origin/main latest branch policy
published_to_root: vue3/
published_at_commit: 40e061bb1fdc5a841071a9ba88354fc1395a80fe
---

# V-1.7.0 /edge/ros 长连接入口 + edge-relay transport

## 本轮结论

本轮把 V 线 backend 从“REST 控制中心”扩展为“REST + `/edge/ros` WSS 控制中心”。

两条链路并存：

- 本地联调链：`前端 -> backend -> rosbridge -> ROS -> OpenRF1`
- 云端联调链：`前端 -> backend <- WSS /edge/ros <- edge-relay(Pi) -> ROS -> OpenRF1`

本轮不做真实实验室 ROS 联调，只做静态施工与本地 edge-relay 模拟验证。

## 已完成

- `backend/src/app.js` 已拆为只创建 Express app，不再直接 `listen`
- `backend/src/server.js` 创建共享 HTTP server，并挂 `/edge/ros` WebSocket upgrade
- `ROS_TRANSPORT` 已扩展为 `mock | rosbridge | edge-relay`
- 新增 Prisma `EdgeDevice`，设备 token 使用 bcrypt hash 存储
- `/api/ros/*` 外部控制 API 保持不变，edge-relay 只作为内部 transport 扩展
- `/api/integrations/ros/status` 增加 edge-relay 在线状态字段
- 新增 `public-edge` runtime profile 与 Nginx WebSocket 反代配置
- 首页与管理员页增加 edge-relay 状态可视化

## 文档入口

- `docs/releases/V-1.7.0/edge-relay-protocol.md`
- `docs/releases/V-1.7.0/public-edge-deploy.md`
- `docs/releases/V-1.7.0/static-local-simulation.md`
- `docs/releases/V-1.7.0/edge-relay-joint-debug.md`
- `docs/releases/V-1.7.0/edge-relay-local-convergence.md`
- `docs/releases/V-1.7.0/public-edge-env-handoff.md`
- `docs/releases/V-1.7.0/prisma-edge-device-migration-hotfix.md`

## 未完成项

- 未做真实 Pi edge-relay 程序施工
- 未做真实 Pi -> backend -> ROS -> OpenRF1 云端闭环
- 未做设备管理 UI / API
- 未替换本地 rosbridge 链路

## 发布纪律

本轮仍按 V 线制度执行：

- 先在自测分支冻结
- 再只把 `vue3/` supplement merge 到 `main`
- 不覆盖 `Raspberrypi/` 或 C 线目录
