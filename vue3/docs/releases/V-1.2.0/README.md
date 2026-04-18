---
version: V-1.2.0
based_on_branch: feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery
branch_source: GitHub branches page
published_to_root: vue3/
published_at_commit: 46b8bb5584d3e8c1dbb84d7af969826506aca282
---

# V-1.2.0 冻结说明

## 本轮定位

`V-1.2.0` 不推翻 `src/* + backend/*` 现有基线，只在 `V-1.1.0` 之上完成三类增强：

1. 移动端导航从按钮堆叠重构为原生 `tabBar`
2. 管理员页从命令输入页升级为系统管理工作台
3. 为下一轮树莓派 + OpenClaw 联调预埋 backend 适配层

## 版本纪律更新

从本轮开始，V 线版本纪律改为：

- 大轮：`V-1.2.0`
- 同轮子任务：`V-1.2.1`、`V-1.2.2`、`V-1.2.3`、`V-1.2.4`、`V-1.2.5`

不再使用：

- `V-1.2.0A`
- `V-1.2.0B`
- `V-1.2.0C`

## 本轮实例分支

- 云端仓库：`https://github.com/Git-ys1/CleanScout_rover`
- 当前实例分支：`feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery`
- 说明：该分支仅为本轮镜像发布实例；制度上仍然以“发布前在 GitHub branches page 确认的最新施工分支”为准。

## 官方开发依据

### uni-app 官方底层开发手册

- CLI 快速上手：https://uniapp.dcloud.net.cn/quickstart-cli
- 页面与 pages.json：https://uniapp.dcloud.net.cn/collocation/pages
- WebSocket / SocketTask：https://uniapp.dcloud.net.cn/api/request/websocket.html
- Pinia 状态管理：https://uniapp.dcloud.net.cn/tutorial/vue3-pinia.html

### OpenClaw 官方对接手册

- OpenClaw 首页：https://docs.openclaw.ai/zh-CN
- Gateway 运行手册：https://docs.openclaw.ai/zh-CN/gateway
- Gateway 协议：https://docs.openclaw.ai/zh-CN/gateway/protocol
- Web / Control UI / 远程访问：https://docs.openclaw.ai/zh-CN/web/index
- Control UI / SSH 隧道说明：https://docs.openclaw.ai/zh-CN/web/dashboard
- OpenResponses 计划：https://docs.openclaw.ai/zh-CN/experiments/plans/openresponses-gateway

本轮明确写死：后续持续依据 `uni-app` 官方文档与 `OpenClaw` 官方文档开发，不做无依据实现。

## V-1.2.1：移动端导航重构

本轮前端主导航改为原生 `tabBar`，一级入口固定为：

- 首页：`pages/index/index`
- 对话：`pages/chat/index`
- 我的：`pages/profile/index`

落地结果：

- `src/pages.json` 已新增 `tabBar`
- 新增 `src/static/tabbar/` 图标资源
- 首页已删除一级跳转按钮堆叠，只保留总览信息
- 管理员入口已迁移到个人中心，仅 `admin` 角色可见

## V-1.2.2：管理员能力升级 backend

本轮后端在 `User` 模型上新增：

- `isEnabled Boolean @default(true)`

并新增单例配置模型：

- `SystemConfig`
  - `registrationEnabled`
  - `appEnabled`
  - `maintenanceMessage`
  - `openclawEnabled`

新增管理员接口：

- `GET /api/admin/users`
- `POST /api/admin/users`
- `PATCH /api/admin/users/:id`
- `DELETE /api/admin/users/:id`
- `GET /api/admin/system-config`
- `PATCH /api/admin/system-config`

冻结规则：

- 禁止删除自己
- 禁止删除最后一个管理员
- 禁止把最后一个管理员降级成 `user`
- 停用用户无法登录
- 关闭注册后，`/api/auth/register` 返回 `AUTH_REGISTRATION_DISABLED`
- 关闭软件可用后，普通用户业务接口返回 `SYSTEM_MAINTENANCE`

## V-1.2.3：管理员工作台 frontend

管理员页已从单一命令输入页升级为三段式工作台：

- 用户管理
- 系统开关
- 设备 / 网关接入状态

前端新增：

- `src/stores/admin.js`

当前管理员工作台支持：

- 查看用户列表
- 新增用户
- 启用 / 停用用户
- user/admin 角色切换
- 删除用户
- 修改注册开关、软件总开关、维护提示语、OpenClaw 软开关
- 刷新 OpenClaw 接入状态

## V-1.2.4：OpenClaw backend adapter

本轮 OpenClaw 接入方向冻结为：

```text
uni-app 前端 -> backend -> OpenClaw Gateway -> 树莓派 / 设备侧
```

本轮只接 OpenClaw HTTP 兼容面，不接 Gateway WebSocket 控制协议。

新增目录：

```text
backend/src/integrations/openclaw/
├─ client.js
├─ service.js
└─ types.js
```

新增环境变量：

```text
OPENCLAW_ENABLED=false
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_API_MODE=chat
OPENCLAW_MODEL=openclaw/default
OPENCLAW_BEARER_TOKEN=
OPENCLAW_REQUEST_TIMEOUT_MS=30000
```

新增接口：

- `GET /api/integrations/openclaw/status`

聊天 transport 规则：

- `OPENCLAW_ENABLED=false` 或后台软开关关闭：走 `mock`
- OpenClaw 探测健康：转发 `POST /v1/chat/completions`
- `OPENCLAW_API_MODE=responses` 时：切换到 `POST /v1/responses`
- OpenClaw 探测失败或调用失败：自动回退 `mock`，并在响应里显式返回 `transport`

`POST /api/chat/send` 当前响应结构：

```json
{
  "success": true,
  "data": {
    "userMessage": {},
    "replyMessage": {},
    "transport": {
      "mode": "mock | openclaw",
      "fallback": true,
      "status": "disabled | healthy | degraded | error",
      "message": "string",
      "model": "openclaw/default",
      "apiMode": "chat | responses"
    }
  }
}
```

## 当前验证结果

本轮已完成以下验证：

- `cmd /c npm.cmd run build:h5` 通过
- `GET /api/system/health` 通过
- `GET /api/integrations/openclaw/status` 在默认环境下返回 `status=disabled`
- `POST /api/chat/send` 在默认环境下返回 `transport.mode=mock`
- 临时以进程级环境变量强开 `OPENCLAW_ENABLED=true` 后，`GET /api/integrations/openclaw/status` 返回 `status=error`
- 同一条件下，`POST /api/chat/send` 返回 `transport.fallback=true`
- 管理员后台已验证用户管理、系统开关和接入状态刷新链路

## 下一轮联调路径

下一轮树莓派联调优先采用：

```text
SSH 隧道
ssh -N -L 18789:127.0.0.1:18789 user@host
```

结论：

- 树莓派上的 OpenClaw 继续保持 `loopback`
- backend 继续请求本机 `http://127.0.0.1:18789/v1/...`
- 热点局域网直连仅作为次优方案，不作为默认路径

## 本轮未完成项

本轮明确未完成：

- 真实树莓派联调
- 真实 OpenClaw 在线对话
- 真实设备状态接入
- Gateway WebSocket 控制协议
- 复杂 RBAC
- 多设备管理

## 发布说明

- 本轮本地提交按 `V-1.2.1` 至 `V-1.2.5` 分步留痕
- 云端镜像发布目标仍为当前最新施工分支根目录下的 `vue3/`
- `published_at_commit` 当前记录的是本轮 OpenClaw 适配层完成后的本地主仓冻结提交
