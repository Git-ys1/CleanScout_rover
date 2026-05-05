# V-1.9.0 前端体验热优化冻结记录

```text
version: V-1.9.0
scope: frontend-visual-hot-optimization
backend_protocol_changed: false
ros_edge_openclaw_changed: false
```

## 本轮结论

本轮只做前端体验热优化，不改后端协议、ROS、edge-relay、OpenClaw、ASR 和风机控制接口。

执行准则来自：

- `docs/2026-05-04-Vibe coding前端干货！4种方法提升页面质感.md`
- 当前 live H5 页面审查
- 现有 uni-app Vue3 工程结构

本轮没有新增“提示词交付文档”。设计提示词作为执行准则使用，不作为仓库产物。

## 已完成改动

1. 设计系统收口

- 新增 `src/styles/tokens.scss`
- 重构 `src/uni.scss`
- 在 `src/App.vue` 落地全局 CSS 变量、卡片、页面、按压、淡入等基础 utility
- 状态标签统一改为低饱和彩色 chip，并保留中文语义映射

2. 首页重构

- 首页从“实验台模块堆叠”改为产品化主控台
- 首屏聚焦设备身份、前视画面、快捷控制
- 设备状态和连接状态变成轻量摘要卡
- ROS 遥测和双风机系统下沉到“更多状态”
- 风机 PWM 保持现有接口，仍支持滑条变更后自动下发与手动立即同步

3. 对话页重构

- 删除首屏大段研发说明
- 保留细粒度链路状态条
- 强化左右气泡层级
- 输入区继续吸底，但改为更紧凑的移动端聊天输入器
- 新增建议词：`前进`、`停止`、`查看状态`、`打开风机`，只回填输入框，不新增协议

4. 个人中心与管理后台重构

- 个人中心改为账户页：头像、用户名、角色、后端入口、设备链路、管理员入口
- 移除 token 摘要展示
- 管理后台改为系统管理台：概览卡、sticky 分段、用户管理、系统开关、接入状态
- 保留原有管理接口与业务行为

## 工具与审查

VS Code 插件检查：

- 已安装 `Vue.volar`
- 已安装 `dbaeumer.vscode-eslint`
- 已安装 `esbenp.prettier-vscode`
- 已安装 `usernamehw.errorlens`

浏览器审查：

- 使用现有 Playwright 浏览器能力访问 live H5 与本地 H5
- 已覆盖 `390x844`
- 已补充首页 `375x812` 与 `430x932`

可访问性记录：

- 状态不只靠颜色表达，继续显示中文状态文字
- 控制按钮、聊天输入、语音按钮均保留可识别中文文本
- 主要危险操作使用红色系加文字说明
- 本轮未自动调用 Accessibility Insights 扩展
- 尝试用 `npx.cmd lighthouse` 跑本地 H5，对话页可进入采集流程，但 Lighthouse CLI 在 Windows 临时目录清理阶段返回 `EPERM`；报告文件不纳入仓库，结果以 Playwright 视口截图、中文可识别控件和构建验证为主

## 截图索引

Before：

- `screenshots/before-home-390.png`
- `screenshots/before-chat-390.png`
- `screenshots/before-profile-390.png`
- `screenshots/before-admin-390.png`

After：

- `screenshots/after-home-390.png`
- `screenshots/after-chat-390.png`
- `screenshots/after-profile-390.png`
- `screenshots/after-admin-390.png`

移动视口：

- `screenshots/viewport-home-375.png`
- `screenshots/after-home-390.png`
- `screenshots/viewport-home-430.png`

## 验证命令

已执行：

```bash
cmd /c npm.cmd run build:h5:production
cmd /c npm.cmd run build:mp-weixin:production
```

本地前后端热验证：

```text
backend: http://127.0.0.1:3000/api/system/health -> service=ok, database=ok
H5: http://localhost:5173 -> 200 OK
```

## 未改内容

- 未改 `/api/chat/send`
- 未改 `/api/ros/*`
- 未改 `/edge/ros`
- 未改 OpenClaw transport
- 未改 ASR 上传与识别接口
- 未改风机控制接口

## 后续建议

下一轮可以让项目负责人直接访问云端 H5：

```text
https://h5.hzhhds.top
https://cleanscoutrover-management.netlify.app
```

重点看：

- 首页首屏是否符合设备控制产品气质
- 对话页是否适合作为 OpenClaw 自然语言入口
- 管理后台是否需要拆成更细的二级页面
- 风机与底盘控制是否要进一步做“安全确认 / 长按控制 / 操作锁”
