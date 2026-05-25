# pc-openclaw-worker

CleanScout 的本机 OpenClaw Worker。

职责：

1. 主动连接云端后端 WebSocket
2. 接收 OpenClaw 对话请求
3. 本机调用 OpenClaw Gateway
4. 把结果回传云端后端

## 当前阶段定位

1. 不直接控制底盘
2. 不直接做 ROS 节点
3. 不直接暴露 OpenClaw Dashboard 到公网

## 目录

```text
tools/pc-openclaw-worker/
  package.json
  .env.example
  .env.local
  src/
    index.js
    probe.js
    config.js
    cloudClient.js
    openclawClient.js
```

## 环境变量

首次使用：

```bash
cp .env.local .env
```

## 本地 Probe 模式

后端尚未完成前，先只做本机自检：

```bash
npm install
npm run probe
```

Probe 模式会：

1. 探测 `GET /v1/models`
2. 探测 `POST /v1/chat/completions`
3. 打印模型列表和回复结果
4. 不连接云端后端

## 正式 worker 模式

```bash
npm install
npm start
```

## 当前完成度

1. 已对齐云端 main 的 worker 结构思路
2. 已具备本机 OpenClaw probe 能力
3. 已具备云端 WebSocket 注册 / 心跳 / 对话结果回传骨架
4. 等待后端工程师完成云端接口后联调
