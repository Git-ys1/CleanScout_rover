# BS 多模态 Agent

独立的终端文字聊天和网页图文聊天示例，通过 Agnes API 生成回复。基于教学 step04 的系统提示词和 history 结构扩展，默认角色“诺登”可在 agent.py 中修改。

本示例部署在 CleanScout_rover 的 vue3/bs/。尚未接入原有 Express 后端、账户体系或 Vue 消息页。

## 首次运行

在 VS Code 终端进入本目录。Windows x64 可下载独立 Python 到本目录：

```powershell
.\setup-python.cmd
# 仅首次复制，已有 .env 不要覆盖
Copy-Item .env.example .env
# 用编辑器填写 .env 中的 AGNES_API_KEY
.\chat.cmd
```

已有 .python 和 .env 可直接运行 chat.cmd。输入 /new 清空上下文，/exit 或 Ctrl+C 退出。终端只保留最近 20 轮，退出后不保存。

网页模式：

```powershell
.\web.cmd
```

保持终端运行，打开 http://127.0.0.1:8000 。支持文字、上传图片和公网 HTTPS 图片地址。网页和终端会话独立。修改提示词后重启程序，开始新会话。

.cmd 启动不需要更改 PowerShell 脚本执行策略。也可直接运行 .\.python\python.exe -B agent.py 或 server.py。其他平台可用 Python 3.10+ 直接运行，无需第三方包。

## 独立环境

setup-python.cmd 下载官方 Python 3.13.15 Windows x64 embeddable 包，校验 SHA-256 后解压到 .python，并在 python313._pth 添加 .. 以导入本目录模块。已有 .python 时停止，避免覆盖。环境不含 pip，当前程序只需标准库，不修改 PATH、注册表或其他工程。

官方来源：https://www.python.org/downloads/release/python-31315/

SHA-256：d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf

.python、下载包、.env、data/ 均被 Git 忽略，克隆后需自行初始化。
VS Code 单独打开本目录时，项目设置提供本目录解释器路径；打开整个仓库时，可手动选择 vue3/bs/.python/python.exe。

## 数据与 API

Key 只在后端读取；对话和图片发送给 Agnes 云端推理。默认模型 agnes-2.5-flash，接口 POST https://apihub.agnes-ai.com/v1/chat/completions。图片通过 image_url 内容块传入，本地上传使用已实测的 Data URL。支持 PNG/JPEG/WEBP/GIF，单张上限 5 MB。

官方接口文档：https://agnes-ai.com/en/docs/agnes-25-flash

网页消息持久化到 data/messages.sqlite3，图片可能随消息以 Base64 保存。模型接收最近 20 轮，页面恢复最近 100 轮，更早记录仍在数据库。未实现长期记忆总结。

```text
POST /api/chat
Content-Type: application/json

{"session_id":"chat-001","message":"图里有什么？","image":"https://example.com/photo.jpg"}

响应：{"reply":"模型生成的回复"}

GET /api/messages?session_id=chat-001
响应：{"messages":[{"role":"user","content":...},{"role":"assistant","content":"..."}]}

GET /api/status
响应：{"configured":true}
```

纯文字省略 image。仅监听本机，定位为单人开发示例，没有账户认证，不适合直接暴露到公网。请求串行执行，客户端不自动重试，尚未实现重试幂等。

## 验证

```powershell
.\.python\python.exe -B -m unittest -v
```

5 项本地测试覆盖图文流程、会话隔离、失败不落库、参数/私有文件限制、图片编码与缺少密钥提示。

check_live.py 为手动真实 API 测试，会使用服务额度，仅发送文字与合成几何图。2026-09-05 已验证文字回复、红色正方形/蓝色圆形识别、图片追问及 HTTP 图文消息保存。未做浏览器自动化测试。角色遵循受上游模型影响。

连接被拒绝时确认 web.cmd 正在运行；数据库报错时确认当前用户能写入 data/。开发工具沙箱可能限制写入或网络，可在自己的 VS Code 终端启动。

## 文件

- agent.py：角色、配置、Agnes 请求、终端循环。
- server.py：HTTP、会话与 SQLite。
- index.html：图文聊天页面。
- chat.cmd / web.cmd / start.ps1：启动入口。
- setup-python.cmd：Windows 运行环境初始化。
- .env.example：不含 Key 的配置示例。
- test_agent.py / check_live.py：本地与真实 API 验证。

## 后续提交

建议在 Fork 的开发分支内维护本目录。若在仓库外的 bs 开发，提交前将源码同步至 vue3/bs，排除密钥、数据库、解释器和下载包。

在仓库根目录执行：

```powershell
git status
git add vue3/bs
git diff --cached --stat
git commit -m "feat: update BS agent"
git push origin HEAD
```

未合并 PR 会随同一分支的 Push 更新。PR 合并后，基于最新 upstream/main 新建分支和 PR。主仓库维护者审核合并后才进入主仓库，不会自动同步。
