---
version: V-1.1.0
based_on_branch: feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery
branch_source: GitHub branches page
published_to_root: vue3/
published_at_commit: 2040a4beb597c98a3de7d1de7d891f1d6c3f32d7
---

# V-1.1.0 实际业务开发第一轮冻结说明

## 本轮目标

`V-1.1.0` 是 V 线从立项冻结转入实际业务开发的第一轮。

本轮只做三件事：

1. 搭起前端壳子，打通登录、注册、首页、聊天、管理员页、个人中心页。
2. 搭起后端鉴权壳子，落地 `Express + Prisma + SQLite + bcrypt + jsonwebtoken`。
3. 先用 mock 接口完成前后端联调，不接真实树莓派、openclaw 和真实设备控制。

## 本轮使用的主施工分支

- 云端仓库：`https://github.com/Git-ys1/CleanScout_rover`
- 本轮实例分支：`feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery`
- 说明：该分支只是本轮发布实例；制度上仍然以“发布前在 GitHub branches page 确认的当前最新施工分支”为准。

## 前端新增页面

本轮新增并在 `src/pages.json` 注册的页面如下：

- `src/pages/auth/login.vue`
- `src/pages/auth/register.vue`
- `src/pages/index/index.vue`
- `src/pages/chat/index.vue`
- `src/pages/admin/index.vue`
- `src/pages/profile/index.vue`

页面职责：

- 登录页：账号、密码、登录、跳注册。
- 注册页：普通用户注册，不开放管理员注册。
- 首页：显示当前用户、mock 设备摘要、最近消息摘要、页面跳转入口。
- 对话控制页：消息历史、输入框、mock 回复。
- 管理员页：管理员命令输入、快捷命令按钮、mock 返回结果。
- 个人中心页：显示当前用户、角色、Token 摘要与退出登录。

## Pinia store 列表

本轮已接入 Pinia，并落地 4 个 store：

- `src/stores/auth.js`
- `src/stores/app.js`
- `src/stores/chat.js`
- `src/stores/device.js`

职责划分：

- `authStore`：`token`、`userInfo`、`role`、`isLoggedIn`，以及 `login`、`logout`、`register`、`fetchMe`、`setToken`、`restoreSession`
- `appStore`：`appReady`、`currentTab`、`loading`、`networkStatus`
- `chatStore`：`messages`、`sending`、`draftText`
- `deviceStore`：`deviceOnline`、`deviceSummary`、`lastTelemetry`、`adminConsoleResult`

## 前端 API 壳子

本轮已建立 API 抽象层：

- `src/api/config.js`
- `src/api/http.js`
- `src/api/auth.js`
- `src/api/device.js`
- `src/api/chat.js`
- `src/api/admin.js`
- `src/api/ws.js`

冻结规则：

- 页面不允许直接写死请求地址。
- 当前实时链路只保留 `SocketTask` 预留位，不建立真实连接。
- H5 联调默认后端基地址为 `http://127.0.0.1:3000/api`。

## 后端目录结构

本轮新增 `backend/` 并采用以下结构：

```text
backend/
├─ prisma/
│  ├─ migrations/
│  ├─ schema.prisma
│  └─ seed.js
├─ src/
│  ├─ controllers/
│  ├─ middleware/
│  ├─ routes/
│  ├─ services/
│  ├─ utils/
│  └─ app.js
├─ package.json
├─ package-lock.json
└─ .env.example
```

## Prisma 模型

本轮已落地 3 个基础模型和 1 个角色枚举：

### `Role`

- `user`
- `admin`

### `User`

- `id`
- `username`
- `passwordHash`
- `role`
- `createdAt`
- `updatedAt`

### `DeviceCache`

- `id`
- `deviceId`
- `summaryJson`
- `updatedAt`

### `MessageCache`

- `id`
- `userId`
- `role`
- `content`
- `createdAt`

## 默认管理员账号 seed 规则

本轮默认管理员账号规则如下：

- 用户名：`admin`
- 密码：`123456`
- 角色：`admin`

约束：

- 禁止明文入库。
- 密码使用 `bcrypt` 哈希。
- seed 可重复运行；若 `admin` 已存在则跳过创建。
- 同时初始化默认设备缓存：`mock-rover-001`

## 当前 mock 接口列表

本轮后端已提供以下接口：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/device/summary`
- `GET /api/chat/history`
- `POST /api/chat/send`
- `POST /api/admin/command`
- `GET /api/system/health`

响应格式冻结为：

- 成功：`{ success: true, data: ... }`
- 失败：`{ success: false, message: "...", code?: "..." }`

## 本轮联调结果

本地已完成以下验证：

- `cmd /c npm.cmd run build:h5` 通过
- `cmd /c npm.cmd run prisma:generate` 通过
- `cmd /c npm.cmd run prisma:migrate` 通过
- `cmd /c npm.cmd run prisma:seed` 通过
- 后端本地服务可启动，`/api/system/health` 返回 `service=ok`、`database=ok`
- 默认管理员 `admin / 123456` 可登录
- 普通用户可注册并登录
- `/api/auth/me`、`/api/device/summary`、`/api/chat/history`、`/api/chat/send`、`/api/admin/command` 已实跑通过
- 普通用户调用管理员接口会返回 `403`

## 本轮未完成项

本轮明确未做：

- 未接真实 openclaw
- 未接真实树莓派
- 未接真实设备控制
- 未落地真实 WebSocket / SocketTask 链路
- 未做复杂 UI 美化
- 未做多设备管理
- 未做复杂 RBAC

## 发布说明

- 本地必须先完成 checkpoint 和分步 commit，再进行云端镜像发布。
- 云端镜像目标仍为当前最新施工分支根目录下的 `vue3/`。
- `published_at_commit` 会在本轮本地发布 commit 与云端镜像发布完成后回填。
