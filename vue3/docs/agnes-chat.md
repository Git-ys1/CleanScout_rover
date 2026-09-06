# 原聊天页面接入 Agnes

入口为 `src/pages/chat/index.vue` → `backend` Express 聊天接口 → Agnes。`bs/` 保留为教学示例，不是正式功能的运行依赖。本次只做用户发送图片、模型返回文字与后续追问，不生成图片、不控制机械臂或车辆。

## 本地启动

需要 Node.js 22.21+（本次验证为 22.23.2）和 npm。以下命令从仓库根目录执行：

```powershell
cd vue3/backend
npm ci
Copy-Item .env.example .env  # 仅首次；不要覆盖已有 .env
```

用编辑器修改服务端 `.env`：

```dotenv
APP_PROFILE=local-lan
PORT=3000
DATABASE_URL="file:./dev.db"
JWT_SECRET="replace-with-your-own-random-secret-at-least-32-characters"
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
CHAT_PROVIDER=agnes
AGNES_API_KEY=
AGNES_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_MODEL=agnes-2.5-flash
AGNES_TIMEOUT_MS=60000
# AGNES_SYSTEM_PROMPT=你的项目提示词
```

填入自己的 Key。Key 只由后端环境读取，不设置任何 `VITE_*` Key，不写进源码、前端或 Git。若使用现有 `ENV_FILE` 启动配置，将上述字段放入该服务端环境文件。默认提示词为 CleanScout 中文图文问答助手，明确不能声称已执行设备控制。

```powershell
npm run prisma:generate
npm run prisma:migrate:deploy
npm run dev
```

新测试环境可以在原系统注册账号后登录。若需要项目已有管理员种子流程，可执行 `npm run prisma:seed`；其默认管理员密码由现有 seed 定义，部署时应按项目流程修改。

另开终端：

```powershell
cd vue3
npm ci
npm run dev:h5
```

打开终端显示的 H5 地址（本地配置默认为 5173）；`.env.h5.local` 指向 `http://127.0.0.1:3000/api`。登录 → 原“对话”页 → 确认顶部显示 Agnes → 选择图片 → 预览并输入问题 → 发送 → 等待文字回答 → 继续追问 → 刷新检查历史及图片。

若后端网络需要已有 HTTP 代理，支持该选项的 Node 版本可用 `node --use-env-proxy src/server.js`，并在进程环境配置 `HTTPS_PROXY` / `HTTP_PROXY`、`NO_PROXY=localhost,127.0.0.1,::1`。不要把本机代理地址硬编码进项目。前端始终直接访问本地 backend。

## 模式与行为

| 配置 | 行为 |
| --- | --- |
| `CHAT_PROVIDER=agnes` | 文字、图片问题、含图片上下文的追问；缺 Key 或模型失败返回错误，不回退 mock |
| `CHAT_PROVIDER=mock` | 明确标为模拟回复，不调用模型、不宣称理解图片 |
| `CHAT_PROVIDER=openclaw`（默认） | 保留现有 OpenClaw 文字入口及硬/软开关；关闭时明确显示 mock；已启用但调用失败时返回错误 |

OpenClaw 当前接口未提供视觉消息适配，启用 OpenClaw 时上传图片会返回明确的“不支持”错误，请选择 Agnes 进行本次图文验收。`GET /api/chat/status` 是正式聊天页模式来源，不再拿 Worker 状态冒充 Agnes 状态。`AGNES_TIMEOUT_MS` 为 100–120000 毫秒，默认 60000；前端聊天请求等待上限 150 秒。

所有聊天接口复用 `authRequired`、`appAvailabilityRequired`。文本和图片 API 均接受 `requestId`；图片 multipart 另带 `content` 作为问题。新页面选图不会立即发送。

## 历史、图片和重试

- Prisma `MessageCache` 保存原图片地址、文件名、MIME、问题与 AI 回答。上下文只取当前用户最近 24 条消息，倒序查询后转正序；页面恢复最近 100 条，更早记录仍在数据库。
- 模型上下文最多包含最近 4 张图片，超出部分替换为明确的图片已省略标记；需要讨论窗口外图片时请重新上传。
- 继续保留 JPEG/PNG/GIF/WebP 白名单、文件签名与声明 MIME 匹配检查，以及单图 10 MB 限制。模型收到的是读取后的 Base64 Data URL，不是 `/uploads/...` 或 localhost 地址。
- `/uploads/chat/...` 现在需要 Bearer 登录并检查图片所属用户；前端通过带鉴权的 `downloadFile` 获取预览文件，刷新后重新下载。原有未登录直链无法读取聊天图片；其他 uploads 入口不变。
- `ChatRequest` 新迁移按 `(userId, requestId)` 唯一记录请求摘要、处理状态和成功结果。生成成功后以事务同时保存用户/助手消息及成功结果；失败不插入部分消息，图片写入后若事务失败会清理该文件。
- 同一请求的失败重试复用 ID；成功但客户端丢失响应时返回原结果，不重复插入。ID 对应不同内容返回 409。页面保留当前失败输入，不生成假的助手消息；修改输入会产生新的请求。
- 单个 Express 进程按用户串行处理，各用户互不阻塞；处理中的重复 ID 返回处理中或等待原结果。异常退出后同 ID 的处理权 180 秒后可重新领取；旧处理器无法覆盖新结果。多进程下不同请求的用户顺序未做分布式排队，本轮按单进程部署验收。
- 前端的待发送内容和 ID 在当前页面状态中保存；刷新会恢复服务端已成功记录，但不会恢复尚未成功的本地草稿。失败后建议直接用当前输入重试，网络中断后先检查历史再另发新消息。
- 登出/切换账号会清空聊天状态，旧账号晚到的响应不会写入新账号页面。

已有数据库先应用新迁移；不要删除数据库来“修复”迁移，也不要把数据库、uploads 或真实私聊提交到 Git。

## 可重复自动测试（不使用真实模型）

```powershell
cd vue3/backend
npm ci
npm run prisma:generate
npm run test:chat

cd ..
npm ci
npm run test:chat-store
npm run build:h5
```

后端测试创建 `.test-tmp/` 临时 Prisma 库、临时用户与本地 HTTP 模型桩，完成后清理；覆盖图文请求、图片追问、最近历史、用户隔离、鉴权图片恢复、重复请求、超时/HTTP/空回复/网络错误以及 OpenClaw/mock 入口。
测试内会在明确 mock 模式运行原 `smoke:chat-image`。也可对单独的 mock 测试服务运行：

```powershell
$env:SMOKE_BASE_URL='http://127.0.0.1:3000'
$env:SMOKE_USERNAME='你的测试用户'
$env:SMOKE_PASSWORD='你的测试密码'
npm run smoke:chat-image
```

旧 smoke 的合法 PNG 用例只含文件头，目的是校验既有签名规则，不是有效真实视觉图片；不要将其当作真实 Agnes 识图验收。

前端测试运行实际 Pinia store，模拟 uni 网络/上传/下载 API，覆盖先选图后发送、错误不伪装回答、重试 ID、历史预览和账号切换。H5 构建是编译检查，不等于浏览器端到端验收。

2026-09-06 最终执行：后端 17 个子用例全部通过（Node 报告含外层套件为 18/18），前端 4 个子用例全部通过（含外层为 5/5），原 smoke 回归通过，`build:h5` 成功。构建输出有工具链循环依赖警告，不影响本次编译成功。未执行浏览器端到端自动化。

## 真实 Agnes 验收（单独执行）

服务端进程环境设置 `AGNES_API_KEY` 后，在 backend 运行 `npm run verify:chat-live`。需要代理时可使用 `node --use-env-proxy scripts/live-chat-agnes.mjs`。

脚本创建临时数据库与测试用户，通过原注册/登录、图片、文字、历史和图片读取接口请求；仅生成一张 300×160 PNG：白底、左侧红色正方形、右侧蓝色圆形。不会读取任何个人照片，不是 OCR 字符测试。测试会消耗真实 API 额度，不属于自动 mock 测试。

2026-09-06 本次实际执行结果（agnes-2.5-flash）：

- 问题：“请用中文描述图中两个图形的形状、颜色和左右位置。”
- 实际回答：“左边是一个红色正方形，右边是一个蓝色圆形。”
- 追问：“右边图形是什么颜色、什么形状？请用中文简短回答。”
- 实际回答：“蓝色圆形。”
- 同次检查通过：历史 4 条记录、带鉴权读取的图片字节等于原图、原请求重试返回同一回复 ID 且不新增记录。

以上是 Express HTTP 级真实验收。未用真实私人照片，未据此声称任意角色照片识别准确，也未将 mock 返回当作视觉结果。
