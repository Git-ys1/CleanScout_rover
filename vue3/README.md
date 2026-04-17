# V线软件交互系统线

## 项目定位

本工程是 V 线的本地主仓，当前定位不再是“仅前端页面项目”，而是本项目的软件交互系统线。

从 `V-1.0.1` 起，V 线按三层软件系统统一定义：

1. 前端端：基于 uni-app + Vue3 + CLI，承担用户交互、对话控制、设备状态展示、管理员直接控制，以及后续 App/H5/小程序多端适配。
2. 后端端：承担多账户登录、账号与权限、设备绑定关系、OpenClaw 转发数据缓存、消息中转、状态持久化，以及对前端暴露统一 API/WS 接口。
3. 设备网关端：由树莓派 + OpenClaw 转发链继续承担设备实时状态来源、指令转发和执行结果回传。

`V-1.0.1` 负责立项补充、制度冻结和文档冻结；`V-1.1.0` 开始进入实际业务开发第一轮，正式落地前端壳子、后端鉴权壳子和 mock 联调链路。

## 系统架构

当前冻结的系统结构为：

```text
用户 / 管理员
        |
        v
前端端（uni-app + Vue3 + CLI）
        |
        v
后端端（账户 / 缓存 / API / 权限 / 消息协调）
        |
        v
设备网关端（树莓派 + OpenClaw 转发链）
        |
        v
巡检车 / 设备侧
```

系统边界结论：

- V 线最终不是纯前端项目，而是前端 + 后端 + 设备接入协议协同的软件系统。
- 当前本地仓 `vue3/` 已同时承载前端工程、`backend/` 后端工程与 release 文档。
- `backend/` 从 `V-1.1.0` 起正式落地，用于账户、权限、缓存和 mock API 联调。

## 技术基线

前端技术栈冻结为：

- 框架：uni-app
- 语法：Vue3
- 创建方式：CLI
- 当前本地工程名：`vue3`
- 当前源码层级：`src/*`
- 当前版本形态：JavaScript

当前工程目录规则继续按现仓真实结构落地：

- 页面文件位于 `src/pages/`
- 工程关键文件位于 `src/App.vue`、`src/main.js`、`src/pages.json`、`src/manifest.json`
- 虽然源码位于 `src/`，但 `pages.json` 中的页面路径仍按 uni-app 约定填写 `pages/...`
- 每次新建页面都必须同步更新 `src/pages.json`
- 未在 `pages.json` 注册的页面，不得视为有效页面

前端基线补充冻结为：

- 实时通信基线：`SocketTask`
- 状态管理基线：`Pinia`

后端技术栈冻结为：

- Web 框架：`Express`
- ORM：`Prisma`
- 数据库：`SQLite`
- 密码哈希：`bcrypt`
- 鉴权令牌：`jsonwebtoken`

## 当前主分支追踪规则

V 线云端镜像发布从 `V-1.0.1` 起按以下制度执行：

主项目云端仓库地址：

- 仓库主页：`https://github.com/Git-ys1/CleanScout_rover`
- 当前发布实例分支页面：`https://github.com/Git-ys1/CleanScout_rover/tree/feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery`

1. 每轮发布前，先在主项目 GitHub 分支页面确认“当前最新施工分支”。
2. 确认完成后，再把本轮 `vue3/` 镜像发布到该分支根目录。
3. 发布目标固定为：

```text
<当前最新施工分支根目录>/vue3/
```

4. release 文档必须显式记录以下元数据：
   - `based_on_branch`
   - `branch_source`
   - `published_to_root`
   - `published_at_commit`
5. V 线可以在本地独立开发，但冻结结果不得长期漂移在过时分支上。

当前实例分支可写为 `feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery`，但它只是当轮实例，不是长期固定分支。制度始终以“发布前确认的最新施工分支”为准。

## 官方开发依据

从 `V-1.2.0` 起，V 线后续持续依据 `uni-app` 官方文档与 `OpenClaw` 官方文档开发，不做无依据实现，不再靠记忆或临时写法施工。

### uni-app 官方底层开发手册

从 `V-1.0.1` 起，以下四份 uni-app 官方文档不再叫“参考链接”，统一提升为“V线官方底层开发手册”：

### 手册 A：uni-app CLI 快速上手

用于：

- 创建工程
- 依赖升级
- 运行与发布
- Node / HBuilderX 环境约束
- `npm run dev:%PLATFORM%` 与 `npm run build:%PLATFORM%` 平台命令规范

官方入口：https://uniapp.dcloud.net.cn/quickstart-cli

### 手册 B：页面与 pages.json

用于：

- 页面目录规范
- 页面注册规则
- 首页设置
- 页面管理规则
- 未注册页面会被编译忽略的开发纪律

官方入口：https://uniapp.dcloud.net.cn/collocation/pages

### 手册 C：WebSocket / SocketTask

用于：

- 实时连接
- 消息收发
- 连接状态监听
- 错误处理

官方入口：https://uniapp.dcloud.net.cn/api/request/websocket.html

前端实时通信统一按 `SocketTask` 体系设计，不再以旧式全局 socket API 为基线。

### 手册 D：Pinia 状态管理

用于：

- 应用级状态管理
- 会话状态
- 设备状态
- 管理员状态
- 用户状态

官方入口：https://uniapp.dcloud.net.cn/tutorial/vue3-pinia.html

前端状态层统一按官方 Pinia 接入方式设计，不允许继续在页面里堆临时全局变量充当状态层。

补充工程资料：

- `manifest.json` 仍保留为工程配置资料，但从 `V-1.0.1` 起不再列为手册级入口。

### OpenClaw 官方对接手册

从 `V-1.2.0` 起，以下 OpenClaw 官方文档纳入 V 线长期对接依据：

- OpenClaw 首页：https://docs.openclaw.ai/zh-CN
- Gateway 运行手册：https://docs.openclaw.ai/zh-CN/gateway
- Gateway 协议：https://docs.openclaw.ai/zh-CN/gateway/protocol
- Web / Control UI / 远程访问：https://docs.openclaw.ai/zh-CN/web/index
- Control UI / SSH 隧道说明：https://docs.openclaw.ai/zh-CN/web/dashboard
- OpenResponses 计划：https://docs.openclaw.ai/zh-CN/experiments/plans/openresponses-gateway

当前对接方向冻结为：

- `uni-app 前端 -> backend -> OpenClaw Gateway -> 树莓派 / 设备侧`
- 前端不直接暴露 Gateway token，不直接连 Gateway 控制面
- 本轮先吃 OpenClaw 的 HTTP 兼容面：`/v1/models`、`/v1/chat/completions`、`/v1/responses`
- 下一轮树莓派联调优先使用 `SSH` 隧道，默认不把 Gateway 暴露到热点局域网

## 后端已纳入系统边界

后端从 `V-1.0.1` 起正式纳入 V 线系统边界，不再是“后面再说”的可选项。

后端第一阶段职责冻结为：

1. 账户体系：多账户登录、用户信息、登录态管理。
2. 权限体系：普通用户、管理员、调试/开发权限预留。
3. 设备数据缓存：缓存 OpenClaw 转发来的状态数据、最近消息和最近任务结果。
4. 对前端统一输出接口：REST API、WebSocket/SSE/转发接口。
5. 对设备侧留接口：树莓派 / OpenClaw 消息上送、指令转发回设备。

`V-1.1.0` 已完成 `backend/` 工程初始化，当前后端承担：

- `/api/auth/register`、`/api/auth/login`、`/api/auth/me`、`/api/auth/logout`
- `/api/device/summary`
- `/api/chat/history`、`/api/chat/send`
- `/api/admin/users`、`/api/admin/system-config`、`/api/admin/command`
- `/api/integrations/openclaw/status`
- `/api/system/health`

当前阶段仍未接入真实树莓派 / OpenClaw，也未落地复杂 RBAC、多设备管理和真实 WebSocket 链路。后续阶段继续为以下内容扩展：

- `api schema`
- `user model`
- `device model`
- `message model`

## 目录口径

任务书中的概念目录在本仓的实际落点如下：

- `pages/` 对应 `src/pages/`
- `components/` 对应 `src/components/`
- `stores/` 对应 `src/stores/`
- `api/` 对应 `src/api/`
- `composables/` 对应 `src/composables/`
- `utils/` 对应 `src/utils/`
- `types/` 对应 `src/types/`
- `mocks/` 对应 `src/mocks/`

当前冻结后的工程结构口径：

```text
vue3/
├─ backend/
│  ├─ prisma/
│  ├─ src/
│  │  └─ integrations/
│  │     └─ openclaw/
│  ├─ package.json
│  └─ .env.example
├─ docs/
│  └─ releases/
│     ├─ V-1.0.0/
│     ├─ V-1.0.1/
│     ├─ V-1.1.0/
│     └─ V-1.2.0/
├─ src/
│  ├─ pages/
│  ├─ components/
│  ├─ stores/
│  ├─ api/
│  ├─ composables/
│  ├─ utils/
│  ├─ types/
│  ├─ mocks/
│  ├─ App.vue
│  ├─ main.js
│  ├─ pages.json
│  ├─ manifest.json
│  └─ uni.scss
├─ README.md
├─ package.json
├─ vite.config.js
└─ .gitignore
```

说明：

- `src/*` 仍然是前端源码唯一有效层级，不允许把示意目录误写为根级 `pages/`、`stores/`、`api/` 并覆盖现有 CLI 工程结构。
- `backend/` 为本仓后端目录，当前仅服务于本地 H5 联调与 mock 接口验证。

## 文档级冻结接口与规则

从 `V-1.0.1` 起，以下规则以文档级 contract 形式冻结：

- 发布追踪元数据：`based_on_branch`、`branch_source`、`published_to_root`、`published_at_commit`
- 前端实时通信基线：`SocketTask`
- 前端状态管理基线：`Pinia`
- 后续系统建模预留：`user model`、`device model`、`message model`

## Git 与发布纪律

- 当前目录是 V 线本地主仓。
- 开工前必须先建 checkpoint，再开始本轮改动；没有 checkpoint 不得开工。
- checkpoint 必须以 Git 留痕为准，至少保证当前冻结结果已有可回溯提交。
- 开工后必须持续 Git 留痕，本地有效成果不得只停留在工作树。
- 从 `V-1.2.0` 起，第三位编号代表同一大轮中的不同任务，统一使用 `V-1.2.1`、`V-1.2.2`、`V-1.2.3` 这类编号，不再使用 `A/B/C`。
- 后续提交统一使用 `V-?.?.?: 做了……` 的结构，不使用口语化提交信息。
- 从 `V-1.0.1` 起，提交标题统一使用中文；版本号、分支名、`Git`、`GitHub`、`Pinia`、`SocketTask` 等关键词保留英文。
- 推荐提交标题示例：`V-1.0.1: 冻结系统补充文档与 Git 发布纪律`
- 每轮冻结结果需要同步到云端主仓当前最新施工分支根目录下的 `vue3/`。
- 云端镜像发布至少包含：
  - `vue3/`
  - `vue3/README.md`
  - `vue3/docs/releases/V-?.?.?/README.md`
- `docs/releases/V-1.0.1/README.md` 中必须写明 `based_on_branch`、`branch_source`、`published_to_root`、`published_at_commit`。
- 云端发布前，必须先完成本地 commit，再执行发布。
- 未同步到云端主仓的结果，不算正式冻结完成。

## 编码纪律

- 仓库内新增、读取、编辑、导出的文本文件统一使用 UTF-8。
- PowerShell 读取文本时显式使用 `Get-Content -Encoding utf8`。
- PowerShell 写入文本时显式使用 `Set-Content -Encoding utf8` 或 `Out-File -Encoding utf8`。
- 后续任何脚本、生成器、代码工具和人工维护动作，都不得再依赖系统默认编码或自动猜测编码。
- 仓库通过 `.editorconfig` 和 `.vscode/settings.json` 固定 UTF-8 为默认编码。

## 运行与验证

Windows PowerShell 环境下优先使用 `npm.cmd`，不要直接使用 `npm`，避免命中 `npm.ps1` 执行策略限制。

前端推荐命令：

```powershell
cmd /c npm.cmd install
cmd /c npm.cmd run build:h5
cmd /c npm.cmd run dev:h5
Get-Content -Encoding utf8 README.md
```

后端推荐命令：

```powershell
cd backend
cmd /c npm.cmd install
cmd /c npm.cmd run prisma:generate
cmd /c npm.cmd run prisma:migrate
cmd /c npm.cmd run prisma:seed
cmd /c npm.cmd run dev
```

`V-1.1.0` 当前本地联调口径：

- 前端 H5 默认使用 `http://127.0.0.1:3000/api` 作为 API 基地址
- 后端 CORS 放通 `localhost` / `127.0.0.1` 的本地开发端口，避免 `uni` 因端口占用切换到新端口时被拦截
- 默认管理员账号通过 seed 初始化：`admin / 123456`
- `OpenClaw` 当前通过 backend 适配层接入，状态探测接口为 `/api/integrations/openclaw/status`
- `OpenClaw` 硬开关来自 `.env` 的 `OPENCLAW_ENABLED`，软开关来自后台 `SystemConfig.openclawEnabled`

`V-1.0.1` 文档补充通过标准：

- `docs/releases/V-1.0.1/README.md` 与 `docs/releases/V-1.0.1/V-1.0.1_project_supplement.md` 同时存在
- 根 `README.md` 已升级为“软件交互系统线”口径
- 根 `README.md` 已明确主分支追踪规则、官方底层开发手册、后端已纳入系统边界
- V-1.0.0 release 文档保持历史快照不回写
