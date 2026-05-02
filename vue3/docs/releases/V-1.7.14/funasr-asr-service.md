# V-1.7.14 FunASR 服务接入说明

## 服务目录

```text
services/funasr-asr/
```

## 模型冻结

- 主 ASR：`paraformer-zh`
- VAD：`fsmn-vad`
- 标点恢复：`ct-punc`

## 运行前置

- Python `>= 3.8`
- `ffmpeg`
- `torch`
- `torchaudio`

## 安装

```bash
cd services/funasr-asr
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动

```bash
cd services/funasr-asr
uvicorn app:app --host 127.0.0.1 --port 7001
```

## backend 环境变量

```text
ASR_ENABLED=true
ASR_PROVIDER=funasr
ASR_BASE_URL=http://127.0.0.1:7001
ASR_LANGUAGE=zh
ASR_REQUEST_TIMEOUT_MS=60000
```

## 服务环境变量

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

`POST /recognize` 输入：

- `file`
- `lang=zh`

返回：

- `text`
- `segments`
- `durationMs`
- `audioFormat`
- `sampleRate`
- `model`
- `language`
