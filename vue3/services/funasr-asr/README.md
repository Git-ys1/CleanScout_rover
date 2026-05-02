# FunASR ASR Service

独立中文语音识别服务，按 `V-1.7.14` 冻结为：

```text
前端录音 -> backend /api/asr/transcribe -> FunASR /recognize -> 文本回填聊天输入框
```

## 技术口径

- 主 ASR：`paraformer-zh`
- VAD：`fsmn-vad`
- 标点恢复：`ct-punc`
- 运行形态：独立 Python 服务
- 输入：`multipart/form-data`
- 转码：`ffmpeg -> 16k mono wav`

## 依赖

按 FunASR 官方说明，运行前至少需要：

- Python `>= 3.8`
- `torch`
- `torchaudio`
- `ffmpeg`

安装仓库内依赖：

```bash
cd services/funasr-asr
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果本机还没有 `torch` / `torchaudio`，请先按官方环境安装。

## 启动

```bash
cd services/funasr-asr
uvicorn app:app --host 127.0.0.1 --port 7001
```

## 环境变量

```text
ASR_SERVICE_PORT=7001
ASR_LANGUAGE=zh
FUNASR_MODEL=paraformer-zh
FUNASR_VAD_MODEL=fsmn-vad
FUNASR_PUNC_MODEL=ct-punc
FUNASR_DEVICE=cpu
FFMPEG_PATH=ffmpeg
```

## 接口

- `GET /health`
- `POST /recognize`

`POST /recognize` 需要：

- `file`
- `lang=zh`
