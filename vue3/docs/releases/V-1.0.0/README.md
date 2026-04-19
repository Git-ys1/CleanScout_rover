# V-1.0.0 冻结说明

## 本轮结论

V 线自 `2026-04-17` 起按“设备前端控制端”正式立项。

本轮只完成以下冻结动作：

- 冻结技术基线：uni-app + Vue3 + CLI
- 冻结源码层级：按 `src/` 组织源码，不做模板重排
- 冻结目录规划、页面规划、通信抽象原则和 Git/发布纪律
- 冻结 UTF-8 编码纪律
- 完成本地主仓初始化
- 完成依赖安装与本地可运行性验证
- 补齐根目录说明文档与本轮 release 文档

本轮未做的事情：

- 未接入真实树莓派/openclaw
- 未实现 mock/ws/http transport
- 未接入 Pinia store
- 未实现业务页面与业务逻辑
- 未完成云端主仓镜像同步

## 当前环境现状

- 工作目录：`f:\Project\CSc——uniapp\vue3`
- 仓位角色：V 线本地主仓
- 当前分支：`feature/v-1.0.0-uniapp-init`
- 包管理入口：Windows 下使用 `npm.cmd`
- 文本编码入口：统一使用 UTF-8
- 当前首页：冻结说明壳层页

补充说明：

- `npm install` 完成后存在上游依赖告警与 `npm audit` 风险提示，本轮不处理依赖治理，因为不属于本轮问题边界。

## 验证命令与结果

已执行：

```powershell
cmd /c npm.cmd install
cmd /c npm.cmd run build:h5
```

补充验证：

- `dev:h5` 做了短时启动检查，检测到本地监听端口 `127.0.0.1:5173`，说明开发服务可拉起。

本轮通过标准对应结果：

- `npm.cmd install`：通过
- `npm.cmd run build:h5`：通过
- `npm.cmd run dev:h5`：通过短时启动检查
- `README.md`：已补齐
- `docs/releases/V-1.0.0/README.md`：已补齐
- `src/pages.json` 首页注册：有效

## 发布要求

本轮发布到云端主仓时，至少同步以下内容：

- `vue3/`
- `vue3/README.md`
- `vue3/docs/releases/V-1.0.0/README.md`

未同步到云端主仓前，本轮只算“本地主仓冻结完成”，不算“云端正式冻结完成”。

## 编码纪律

- 仓库内文本文件统一使用 UTF-8。
- PowerShell 读取文件时显式使用 `-Encoding utf8`。
- PowerShell 写入文件时显式使用 `-Encoding utf8`。
- `.editorconfig` 与 `.vscode/settings.json` 已作为仓库级默认配置写入。

## 本轮冻结内容清单

### 项目定位

- V 线是设备前端控制端，不是展示页项目。
- 第一阶段先做前端控制壳，不单独立后端。

### 页面规划

- 设备首页
- 对话控制页
- 管理员控制页
- 状态/日志页

### 通信抽象原则

- 先抽象 transport，不写死协议
- 先定义状态模型，再做页面模型
- UI 先简单，数据流先正确

### 文档级 contract

- `TransportAdapter`
- `ConnectionState`
- `DeviceState`
- `ConversationMessage`
- `AdminCommand`
- `TelemetrySnapshot`

## 官方参考入口

- uni-app CLI 快速上手：https://uniapp.dcloud.net.cn/quickstart-cli
- pages.json 页面路由：https://uniapp.dcloud.net.cn/collocation/pages
- WebSocket / socketTask：https://uniapp.dcloud.net.cn/api/request/websocket.html
- Pinia：https://uniapp.dcloud.net.cn/tutorial/vue3-pinia.html
- manifest.json：https://uniapp.dcloud.net.cn/tutorial/app-manifest.html
