# V-1.7.14 冻结说明

```text
version: V-1.7.14
based_on_branch: feature/v-1.7.0-edge-relay-cloud-transport
branch_source: local vue3 working branch
published_to_root: vue3/
published_at_commit: pending-local-freeze
```

## 本轮目标

本轮冻结 `FunASR` 中文语音输入接入，路线固定为：

```text
前端录音 -> backend /api/asr/transcribe -> 独立 FunASR ASR 服务 -> 文本回填聊天输入框 -> 用户确认后再发给 OpenClaw
```

## 本轮完成项

- 新增独立 Python `FunASR` 服务目录：`services/funasr-asr/`
- backend 新增：
  - `POST /api/asr/transcribe`
  - `GET /api/integrations/asr/status`
- backend 新增 `ASR_ENABLED / ASR_PROVIDER / ASR_BASE_URL / ASR_LANGUAGE / ASR_REQUEST_TIMEOUT_MS`
- 聊天页新增：
  - 语音录入按钮
  - 录音中 / 识别中 / 失败状态
  - 识别结果回填输入框
- 第一版继续保持“手动确认后发送”，不自动把 ASR 文本发给 `/api/chat/send`

## 本轮未完成项

- 未做真流式 ASR
- 未做自动发送
- 未做语音播报
- 未做语音文件持久化
- 未让 OpenClaw 直接感知音频文件

## 官方依据

- FunASR 官方仓库：<https://github.com/modelscope/FunASR>
- FunAudioLLM / SenseVoice 官方主页：<https://funaudiollm.github.io/>

## 验收口径

- `services/funasr-asr/app.py` 能作为独立 ASR 服务启动入口
- backend 的 `/api/integrations/asr/status` 能在 `ASR_ENABLED=true` 时探测上游服务
- 聊天页可在 H5 / 微信小程序录音后上传音频
- 识别结果默认只回填输入框，不自动发送
