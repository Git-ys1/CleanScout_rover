# V-1.7.14 树莓派 OpenClaw 对齐需求文档

## 目的

本文件用于明确：

- 树莓派侧 `OpenClaw Gateway` 已安装后，还需要做哪些工作才能与当前 `V` 线 backend 对齐
- `V` 线 backend 当前真正吃的是什么接口
- 哪些内容不应该直接暴露给前端

当前冻结结构不变：

```text
前端 -> backend -> OpenClaw Gateway -> 树莓派 / 设备侧
```

不是：

```text
前端 -> OpenClaw Control UI
前端 -> OpenClaw Gateway
```

## 当前 V 线 backend 的对接边界

backend 当前只按 `OpenClaw` 的 HTTP 兼容面接入：

- `GET /v1/models`
- `POST /v1/chat/completions`
- `POST /v1/responses`

当前默认策略：

- 主路径：`/v1/chat/completions`
- 后备路径：`/v1/responses`
- 模型名默认按：`openclaw/default`

当前不接：

- Control UI 网页
- Gateway WebSocket 控制面
- 把 Gateway token 直接暴露给前端

## 树莓派侧必须完成的事项

### 1. Gateway 必须稳定运行

树莓派侧必须保证 `OpenClaw Gateway` 进程已经稳定拉起，而不是只安装完成。

需要至少确认：

- Gateway 已启动
- 监听端口已生效
- 进程重启后可恢复

建议树莓派侧提供的最小自检结果：

- Gateway 启动命令
- Gateway 当前监听地址和端口
- `GET /v1/models` 可访问

### 2. backend 必须能访问到 Gateway

树莓派侧需要明确交付一条 backend 可访问的链路，而不是只说明“本机已经能打开网页”。

当前允许两种方式：

#### 方案 A：局域网直连

适用于：

- backend 跑在本地电脑
- 树莓派和电脑在同一局域网 / 同一热点下

树莓派侧需要交付：

- 可访问的树莓派 IP
- Gateway 端口
- 是否启用了认证

此时 backend 侧将配置为：

```text
OPENCLAW_BASE_URL=http://<树莓派IP>:18789
```

#### 方案 B：loopback + SSH 隧道

适用于：

- 树莓派侧继续保持 Gateway 只绑定本机回环
- 不希望把 Gateway 直接暴露到局域网

树莓派侧需要交付：

- SSH 可达
- 树莓派本机 `127.0.0.1:18789` 上的 Gateway 正常运行

此时由 backend 所在机器建立隧道，例如：

```bash
ssh -N -L 18789:127.0.0.1:18789 <user>@<pi-host>
```

然后 backend 侧继续使用：

```text
OPENCLAW_BASE_URL=http://127.0.0.1:18789
```

### 3. 树莓派侧必须交付认证口径

树莓派侧必须明确：

- Gateway 是否启用了 token / password 鉴权
- 如果启用了 token，必须把 token 明文交给 backend 运维侧配置

backend 当前使用的环境变量为：

```text
OPENCLAW_BEARER_TOKEN=<gateway token>
```

注意：

- token 只进 backend env
- token 不进前端
- token 不写死进仓库代码

### 4. 树莓派侧必须确认模型与接口可用

树莓派侧必须确保当前 Gateway 至少满足：

#### 必需

- `GET /v1/models` 可返回模型列表
- 返回列表里包含 `openclaw/default`

#### 推荐

- `POST /v1/chat/completions` 可用

#### 可选后备

- `POST /v1/responses` 可用

如果树莓派侧没有 `openclaw/default`，或者只开了 Control UI 页面，但没有把 `/v1/*` 兼容面跑通，则当前 backend 无法直接接入。

## backend 侧将采用的配置

树莓派侧对齐完成后，`V` 线 backend 将按以下口径配置：

```text
OPENCLAW_ENABLED=true
OPENCLAW_BASE_URL=http://<树莓派IP或隧道地址>:18789
OPENCLAW_API_MODE=chat
OPENCLAW_MODEL=openclaw/default
OPENCLAW_BEARER_TOKEN=<若开启认证则填写>
OPENCLAW_REQUEST_TIMEOUT_MS=30000
```

同时后台软开关也必须开启：

```text
SystemConfig.openclawEnabled=true
```

也就是说，当前链路需要同时满足：

1. `OPENCLAW_ENABLED=true`
2. `SystemConfig.openclawEnabled=true`
3. backend 能访问 `OPENCLAW_BASE_URL`
4. `/v1/models` 中存在 `openclaw/default`

否则聊天页仍会回退到 `mock`

## 树莓派侧需要回传给 V 线的交付物

树莓派侧完成安装后，必须向 `V` 线提供以下信息：

### 必填

- Gateway 实际访问地址
- Gateway 实际访问端口
- 是否回环绑定
- 是否走局域网直连还是 SSH 隧道
- 是否启用认证
- 若启用认证，对应 token

### 必填验收结果

- `GET /v1/models` 的返回结果
- 是否包含 `openclaw/default`
- `POST /v1/chat/completions` 是否可用
- 如使用 `responses`，`POST /v1/responses` 是否可用

### 建议附带

- Gateway 启动命令
- 进程状态截图或终端输出
- 若失败，提供完整报错而不是只说“网页打不开”

## V 线联调验收标准

树莓派侧完成对齐后，V 线将按以下步骤验收：

1. backend 配置 `OPENCLAW_*` 环境变量
2. 后台打开 `openclawEnabled`
3. 调用：

```text
GET /api/integrations/openclaw/status
```

预期：

- `status=healthy`
- `activeTransport=openclaw`
- `model=openclaw/default`

4. 在聊天页发送文本消息

预期：

- 不再回退 `mock`
- `/api/chat/send` 返回 `transport.mode=openclaw`

## 本轮明确不做的事

- 不让前端直接连 Gateway
- 不把 Control UI 当业务接口
- 不把 Gateway token 暴露给浏览器 / 小程序
- 不要求本轮接 Gateway WebSocket 控制面
- 不要求 OpenClaw 直接处理语音文件

## 当前结论

树莓派侧“装好了 OpenClaw”只代表安装完成，不代表已经与 `V` 线对齐。

要和当前 backend 真正对齐，树莓派侧还必须交付四件事：

1. 让 Gateway 真正运行起来
2. 让 backend 真正能访问到它
3. 把认证方式和 token 交付清楚
4. 确认 `/v1/models`、`openclaw/default`、`/v1/chat/completions` 这条链已可用
