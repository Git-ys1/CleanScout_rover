# 小车平台切换与 OpenClaw 接入任务交接书

## 一、交接背景

本项目后续拟将原板级平台切换到 **Raspberry Pi 4B**，并逐步采用“具身智能”实现思路：让小车具备更强的自然语言交互、任务编排、远程运维与持续记忆能力。树莓派 4B 本身是 64 位四核 Cortex‑A72 平台，常见内存版本为 1GB、2GB、4GB、8GB，并带有千兆网口、双频 Wi‑Fi、蓝牙、USB 3.0 和 40Pin GPIO，适合作为小车上的上位控制与边缘计算主机。([raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/specifications/?utm_source=chatgpt.com))

OpenClaw 官方已提供 Raspberry Pi 4/5 部署路径，并明确建议硬件为 **Pi 4 或 5、2GB 以上内存、16GB 以上 microSD，4GB 更推荐，USB SSD 性能更好**；系统建议使用 **Raspberry Pi OS Lite 64-bit**。([docs.openclaw.ai](https://docs.openclaw.ai/zh-CN/platforms/raspberry-pi?utm_source=chatgpt.com))

## 二、OpenClaw 是什么

OpenClaw 可以理解为一个 **自托管的 AI 网关 / 代理控制中枢**。它把聊天入口、控制界面、AI 模型调用、会话状态、节点注册和远程执行统一起来，让你可以从网页、Telegram 等入口去操作一个持续在线的 AI 助手。官方首页对它的描述是：一个自托管 Gateway，将 WhatsApp、Telegram、Discord 等聊天入口连接到 AI coding agents；而 Gateway 文档进一步说明，它是一个 **长期运行的单进程控制平面**，负责路由、控制、渠道连接，并在一个端口上同时承载 WebSocket 控制、HTTP API、Control UI 等能力。([docs.openclaw.ai](https://docs.openclaw.ai/?utm_source=chatgpt.com))

从系统架构上看，OpenClaw 的 **Gateway** 负责状态、会话、配对、节点注册和渠道连接；如果需要把具体执行能力挂到某台设备上，还可以使用 **Node** 作为远程执行面。官方安全文档明确把 Gateway 定义为“控制平面与策略面”，把 Node 定义为“远程执行面”。([docs.openclaw.ai](https://docs.openclaw.ai/gateway/discovery?utm_source=chatgpt.com))

## 三、为什么这个项目适合接入 OpenClaw

对于小车项目，OpenClaw 最有价值的地方，不是替代底层电机控制，而是充当 **上层智能入口 + 远程运维入口 + 持续记忆入口**。

它适合承担这些事情：

1. 作为“车载智能大脑”的入口：接收自然语言任务，例如“去仓库门口巡检”“回传当前相机状态”“记录本次异常”。
2. 作为“任务调度器”：把感知、定位、路径规划、拍照、语音、日志上传等多个服务串起来。
3. 作为“远程运维界面”：开发人员不一定总在车旁边，但可以通过网页端或 Telegram 远程查看状态、发命令、做恢复操作。
4. 作为“持续记忆层”：OpenClaw 的状态目录和工作区可以保存会话历史、agent 状态、配置、鉴权信息、工作区文件和 memory 文件；官方迁移文档明确说明，复制 `~/.openclaw/` 与 workspace 后，可以保留 config、auth、sessions、channel state、MEMORY.md 等内容。([docs.openclaw.ai](https://docs.openclaw.ai/install/migrating?utm_source=chatgpt.com))

对具身智能项目来说，这意味着：**上层交互和任务理解可以长期积累经验，下层执行模块继续专注实时控制**。这是它最适合这个项目的原因。

## 四、部署到树莓派 4B 的优势

### 1）成本低、易替换、适合原型车

树莓派 4B 成本低、生态成熟、文档多、配件多，比较适合实验室原型验证和项目迭代。它具备网口、Wi‑Fi、蓝牙、USB 3.0、CSI 摄像头接口和 GPIO，作为小车主控或上位机比较顺手。([raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/specifications/?utm_source=chatgpt.com))

### 2）OpenClaw 官方已有 Pi 方案

OpenClaw 官方单独提供了 Raspberry Pi 安装文档，说明这是被明确支持的部署平台，而不是“能不能碰运气跑起来”的状态。官方建议的路径就是：刷写 64 位 Raspberry Pi OS Lite，开启 SSH，安装 Node 24，必要时加 swap，然后安装 OpenClaw 并运行 onboarding。([docs.openclaw.ai](https://docs.openclaw.ai/zh-CN/platforms/raspberry-pi?utm_source=chatgpt.com))

### 3）适合做“常驻网关”

OpenClaw 的核心是 **always-on Gateway**。官方远程访问文档明确建议把 Gateway 跑在一个持续在线的主机上，再通过 SSH 隧道或 tailnet 访问；这正好符合“小车上的树莓派长期在线、开发电脑不一定一直开着”的使用方式。([docs.openclaw.ai](https://docs.openclaw.ai/gateway/remote?utm_source=chatgpt.com))

### 4）适合远程运维

OpenClaw Dashboard / Control UI 官方支持通过 SSH 隧道访问：在远端主机上运行 Gateway，本地通过 `ssh -N -L 18789:127.0.0.1:18789 ...` 转发后，在浏览器访问 `http://127.0.0.1:18789/` 即可。对实验室里的车来说，这种方式比把控制端口直接暴露公网更稳妥。([docs.openclaw.ai](https://docs.openclaw.ai/install/raspberry-pi?utm_source=chatgpt.com))

## 五、项目里建议怎么分工

这里给出一个**推荐架构**，方便后续团队统一认知：

- **底层实时控制层**：电机驱动、编码器、PWM、避障急停、舵机等，仍建议由专门的底层控制模块负责。
- **中间设备层**：树莓派负责摄像头、串口、网络、语音、日志、本地 Python 服务、状态采集。
- **上层智能层**：OpenClaw 负责自然语言交互、任务分解、远程运维、会话与记忆、渠道接入。
- **云端模型层**：调用 OpenAI / Anthropic / Google 等模型 API，或者后续替换为本地模型。官方 FAQ 说明，OpenClaw 既可以跑 API key 方案，也可以跑 local-only models。([docs.openclaw.ai](https://docs.openclaw.ai/help/faq?utm_source=chatgpt.com))

一句话概括：  
**树莓派 + OpenClaw 适合做“会理解任务、能远程维护、可持续记忆”的车载智能中枢；但不建议直接拿它替代高实时性的底层闭环控制。**

## 六、部署流程（入门版）

### 第一步：确认硬件条件

先确认这块树莓派 4B 的内存。官方对 Pi 的建议是 **2GB 起步，4GB 更推荐**；如果只有 2GB 或更低，官方还专门建议加 swap。TF 卡最低建议 **16GB**，但 USB SSD 性能更好。([docs.openclaw.ai](https://docs.openclaw.ai/zh-CN/platforms/raspberry-pi?utm_source=chatgpt.com))

### 第二步：刷系统

建议刷 **Raspberry Pi OS Lite (64-bit)**，因为这是官方 Pi 指南推荐的无头部署方案。刷系统时建议直接在 Raspberry Pi Imager 里预配置主机名、SSH、用户名密码、Wi‑Fi。([docs.openclaw.ai](https://docs.openclaw.ai/zh-CN/platforms/raspberry-pi?utm_source=chatgpt.com))

### 第三步：基础环境准备

启动后先 SSH 进入树莓派，更新系统并安装基础工具。OpenClaw 需要 **Node 22.14+，官方推荐 Node 24**。官方安装器也会自动处理 Node，但在 Linux/Pi 上手动确认 Node 24 会更稳。([docs.openclaw.ai](https://docs.openclaw.ai/install/node?utm_source=chatgpt.com))

### 第四步：必要时添加 swap

如果树莓派是 2GB 或以下，建议按官方 Pi 文档添加 2GB swap，并适当降低 swappiness，避免 OOM。([docs.openclaw.ai](https://docs.openclaw.ai/install/raspberry-pi?utm_source=chatgpt.com))

### 第五步：安装 OpenClaw

官方 Pi 指南给出的标准安装方式是：

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
openclaw onboard --install-daemon
```

其中 onboarding 会引导完成模型鉴权、网关 token、守护进程安装等。文档还说明，对于无头设备，**API key 比 OAuth 更推荐**。([docs.openclaw.ai](https://docs.openclaw.ai/install/raspberry-pi?utm_source=chatgpt.com))

### 第六步：验证运行

官方 Pi 文档建议安装后执行：

```bash
openclaw status
sudo systemctl status openclaw
journalctl -u openclaw -f
```

这样可以确认 Gateway 是否正常、systemd 服务是否拉起、日志是否健康。([docs.openclaw.ai](https://docs.openclaw.ai/install/raspberry-pi?utm_source=chatgpt.com))

### 第七步：访问控制界面

在开发电脑上先取 dashboard URL，再走 SSH 隧道：

```bash
ssh user@gateway-host 'openclaw dashboard --no-open'
ssh -N -L 18789:127.0.0.1:18789 user@gateway-host
```

然后浏览器访问 `http://127.0.0.1:18789/`。官方 Dashboard 文档和 Pi 文档都给了这条路径。([docs.openclaw.ai](https://docs.openclaw.ai/install/raspberry-pi?utm_source=chatgpt.com))

### 第八步：接入手机端入口

如果希望从手机快速操作，官方文档里明确提到 **Telegram 是最快接入的渠道之一**，只需要 bot token，适合作为项目初期的手机控制入口。([docs.openclaw.ai](https://docs.openclaw.ai/start/getting-started?utm_source=chatgpt.com))

## 七、部署后能带来的直接好处

### 1）小车可以变成“随时可叫醒的智能体”

因为 OpenClaw 是常驻网关，只要树莓派通电联网，就可以长期在线接收网页或 Telegram 指令。([docs.openclaw.ai](https://docs.openclaw.ai/gateway?utm_source=chatgpt.com))

### 2）便于多人协作与任务交接

配置、会话、memory、工作区、渠道状态都可以保存在 `~/.openclaw` 与 workspace 中，迁移到新机器时也能一起带走。([docs.openclaw.ai](https://docs.openclaw.ai/install/migrating?utm_source=chatgpt.com))

### 3）对项目后期扩展友好

官方 Gateway 是统一控制面，支持 WebSocket 控制、HTTP API、Control UI 等统一入口，后续要接 Web 控制页、脚本服务、节点、消息渠道，扩展会比较顺。([docs.openclaw.ai](https://docs.openclaw.ai/gateway?utm_source=chatgpt.com))

### 4）安全边界相对清晰

官方默认绑定模式是 `loopback`，并且鉴权默认开启；如果不做额外暴露，控制面默认不会直接裸露到公网，这对实验室设备更安全。([docs.openclaw.ai](https://docs.openclaw.ai/gateway?utm_source=chatgpt.com))

## 八、注意事项

1. **树莓派 1GB 不建议部署**；2GB 勉强可用但一定要注意 swap 和负载；4GB 及以上更适合长期常驻。这个建议来自官方 Pi 要求和树莓派 4B 的内存规格。([docs.openclaw.ai](https://docs.openclaw.ai/zh-CN/platforms/raspberry-pi?utm_source=chatgpt.com))

2. **OpenClaw 更适合做“上层智能编排”**，不建议把高实时闭环控制完全压到它身上。项目中应把“底层控制”和“上层智能”分层处理。

3. **控制界面建议走 SSH 隧道访问**，不要上来就把 UI 直接暴露公网。官方远程访问路线本身就是这么设计的。([docs.openclaw.ai](https://docs.openclaw.ai/gateway/remote?utm_source=chatgpt.com))

4. **无头设备优先用 API key 登录模型提供商**，不要一开始就依赖浏览器 OAuth。官方 Pi 指南明确这样建议。([docs.openclaw.ai](https://docs.openclaw.ai/install/raspberry-pi?utm_source=chatgpt.com))

## 九、给接手同学的一句话说明

如果只用一句话解释这次切换，可以这样说：

**我们准备把树莓派 4B 作为小车上的“持续在线智能主机”，把 OpenClaw 部署在上面，负责自然语言交互、任务编排、远程运维和记忆管理；底层实时控制仍由专门控制模块负责。这样可以让小车从“单次执行的嵌入式设备”升级为“可远程维护、可持续学习、可通过聊天控制的具身智能平台”。**
