from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

import soundfile as sf
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from tts_api import audio
from tts_api.model import TTSService
from tts_api.settings import Settings
from tts_api.stt import STTService

app = FastAPI(title="tts-api", version="0.2.0")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
logger = logging.getLogger("tts_api")

settings = Settings()
tts = TTSService(settings)
stt = STTService(settings)


@app.on_event("startup")
async def _startup() -> None:
    if settings.eager_load:
        await tts.ensure_loaded()
    if settings.stt_eager_load:
        await stt.ensure_loaded()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "model_id": settings.model_id,
            "device": tts.device or "unknown",
        },
    )


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "tts": {
            "model_id": settings.model_id,
            "device": tts.device,
            "dtype": tts.dtype,
            "loaded": tts.is_loaded,
        },
        "stt": {
            "model_id": settings.stt_model_id,
            "loaded": stt.is_loaded,
        },
    }


# ── TTS ──────────────────────────────────────────────────────────────────────

@app.post("/tts")
async def tts_from_ui(
    ref_audio: UploadFile = File(...),
    text: str = Form(...),
    ref_text: str | None = Form(None),
    language: str = Form("Japanese"),
    output_format: str = Form("wav"),
) -> Response:
    return await _synthesize(
        ref_audio, text, ref_text=ref_text, language=language, output_format=output_format
    )


@app.post("/api/tts")
async def tts_api(
    ref_audio: UploadFile = File(...),
    text: str = Form(...),
    ref_text: str | None = Form(None),
    language: str = Form("Japanese"),
    output_format: str = Form("wav"),
) -> Response:
    return await _synthesize(
        ref_audio, text, ref_text=ref_text, language=language, output_format=output_format
    )


async def _synthesize(
    ref_audio: UploadFile,
    text: str,
    *,
    ref_text: str | None,
    language: str,
    output_format: str,
) -> Response:
    fmt = output_format.lower()
    if fmt not in audio.SUPPORTED_OUTPUT:
        raise HTTPException(
            status_code=400,
            detail=f"output_format must be one of {sorted(audio.SUPPORTED_OUTPUT)}",
        )

    suffix = Path(ref_audio.filename or "ref.wav").suffix.lower() or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(await ref_audio.read())

    wav_ref: Path | None = None
    is_wav_temp = False
    try:
        # 入力フォーマットを WAV に正規化してから TTS へ渡す
        wav_ref, is_wav_temp = audio.normalize_to_wav(tmp_path)

        try:
            generated = await tts.synthesize_voice_clone(
                ref_audio_path=str(wav_ref),
                text=text,
                language=language,
                ref_text=ref_text,
            )
        except Exception as e:
            logger.exception("TTS failed")
            raise HTTPException(status_code=500, detail=str(e)) from e

        # 生成音声を一時 WAV に書き出して変換
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_tmp:
            out_wav = Path(out_tmp.name)
        try:
            sf.write(str(out_wav), generated.wav, generated.sample_rate, format="WAV")
            try:
                data = audio.wav_to_format(out_wav, fmt)
            except subprocess.SubprocessError as e:
                raise HTTPException(status_code=500, detail=f"Format conversion failed: {e}") from e
        finally:
            out_wav.unlink(missing_ok=True)

    finally:
        tmp_path.unlink(missing_ok=True)
        if is_wav_temp and wav_ref is not None:
            wav_ref.unlink(missing_ok=True)

    mime = audio.MIME_BY_FORMAT.get(fmt, "audio/wav")
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="tts.{fmt}"'},
    )


# ── STT ──────────────────────────────────────────────────────────────────────

@app.post("/api/stt")
async def stt_api(audio_file: UploadFile = File(...)) -> dict:
    """音声ファイル（wav/mp3/m4a）を文字起こしして JSON で返す。"""
    suffix = Path(audio_file.filename or "audio.wav").suffix.lower() or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(await audio_file.read())

    wav_path: Path | None = None
    is_wav_temp = False
    try:
        wav_path, is_wav_temp = audio.normalize_to_wav(tmp_path)
        try:
            result = await stt.transcribe(wav_path)
        except Exception as e:
            logger.exception("STT failed")
            raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        tmp_path.unlink(missing_ok=True)
        if is_wav_temp and wav_path is not None:
            wav_path.unlink(missing_ok=True)

    return result
