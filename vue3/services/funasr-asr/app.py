from __future__ import annotations

import os
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from funasr import AutoModel


DEFAULT_LANGUAGE = "zh"
DEFAULT_MODEL = "paraformer-zh"
DEFAULT_VAD_MODEL = "fsmn-vad"
DEFAULT_PUNC_MODEL = "ct-punc"
DEFAULT_PORT = 7001
DEFAULT_DEVICE = "cpu"
DEFAULT_SAMPLE_RATE = 16000

app = FastAPI(title="funasr-asr-service", version="1.0.0")
_model_instance: AutoModel | None = None


def get_runtime_config() -> dict[str, Any]:
    return {
        "port": int(os.getenv("ASR_SERVICE_PORT", str(DEFAULT_PORT))),
        "language": os.getenv("ASR_LANGUAGE", DEFAULT_LANGUAGE).strip() or DEFAULT_LANGUAGE,
        "model": os.getenv("FUNASR_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        "vad_model": os.getenv("FUNASR_VAD_MODEL", DEFAULT_VAD_MODEL).strip() or DEFAULT_VAD_MODEL,
        "punc_model": os.getenv("FUNASR_PUNC_MODEL", DEFAULT_PUNC_MODEL).strip() or DEFAULT_PUNC_MODEL,
        "device": os.getenv("FUNASR_DEVICE", DEFAULT_DEVICE).strip() or DEFAULT_DEVICE,
        "ffmpeg_path": os.getenv("FFMPEG_PATH", "ffmpeg").strip() or "ffmpeg",
    }


def get_model() -> AutoModel:
    global _model_instance

    if _model_instance is None:
        config = get_runtime_config()
        _model_instance = AutoModel(
            model=config["model"],
            vad_model=config["vad_model"],
            punc_model=config["punc_model"],
            vad_kwargs={"max_single_segment_time": 30000},
            device=config["device"],
        )

    return _model_instance


def convert_to_wav(input_path: Path, output_path: Path) -> None:
    config = get_runtime_config()
    command = [
        config["ffmpeg_path"],
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        str(DEFAULT_SAMPLE_RATE),
        str(output_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise HTTPException(status_code=502, detail=f"ffmpeg convert failed: {stderr or 'unknown error'}")


def get_wav_duration_ms(wav_path: Path) -> int:
    with wave.open(str(wav_path), "rb") as wav_file:
        frame_count = wav_file.getnframes()
        sample_rate = wav_file.getframerate() or DEFAULT_SAMPLE_RATE

    return int(frame_count / sample_rate * 1000)


def normalize_segments(result: Any) -> list[dict[str, Any]]:
    if not isinstance(result, list):
        return []

    segments: list[dict[str, Any]] = []

    for item in result:
        if not isinstance(item, dict):
            continue

        segment = {
            "text": str(item.get("text", "")).strip(),
        }

        if "timestamp" in item:
            segment["timestamp"] = item["timestamp"]

        if "sentence_info" in item:
            segment["sentenceInfo"] = item["sentence_info"]

        if segment["text"]:
            segments.append(segment)

    return segments


def normalize_text(result: Any) -> str:
    if not isinstance(result, list) or not result:
        return ""

    first = result[0]

    if isinstance(first, dict):
        return str(first.get("text", "")).strip()

    return str(first).strip()


@app.get("/health")
def health() -> dict[str, Any]:
    config = get_runtime_config()

    try:
        get_model()
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"FunASR model load failed: {error}") from error

    return {
        "success": True,
        "data": {
            "status": "healthy",
            "language": config["language"],
            "model": config["model"],
            "message": "FunASR service is ready",
        },
    }


@app.post("/recognize")
async def recognize(file: UploadFile = File(...), lang: str = Form(DEFAULT_LANGUAGE)) -> dict[str, Any]:
    config = get_runtime_config()
    model = get_model()
    language = (lang or config["language"]).strip() or config["language"]

    suffix = Path(file.filename or "recording.bin").suffix or ".bin"

    with tempfile.TemporaryDirectory(prefix="funasr-asr-") as temp_dir:
        temp_root = Path(temp_dir)
        input_path = temp_root / f"input{suffix}"
        output_path = temp_root / "normalized.wav"

        payload = await file.read()
        input_path.write_bytes(payload)

        convert_to_wav(input_path, output_path)

        try:
            result = model.generate(input=[str(output_path)], cache={}, batch_size_s=0)
        except Exception as error:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"FunASR inference failed: {error}") from error

        text = normalize_text(result)
        duration_ms = get_wav_duration_ms(output_path)

        return {
            "success": True,
            "data": {
                "text": text,
                "segments": normalize_segments(result),
                "durationMs": duration_ms,
                "audioFormat": file.content_type or "application/octet-stream",
                "sampleRate": DEFAULT_SAMPLE_RATE,
                "model": config["model"],
                "language": language,
            },
        }


if __name__ == "__main__":
    import uvicorn

    runtime = get_runtime_config()
    uvicorn.run("app:app", host="127.0.0.1", port=runtime["port"], reload=False)
