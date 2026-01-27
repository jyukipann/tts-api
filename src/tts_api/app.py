from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import soundfile as sf
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from tts_api.model import TTSService
from tts_api.settings import Settings


app = FastAPI(title="tts-api", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
logger = logging.getLogger("tts_api")

settings = Settings()
tts = TTSService(settings)


@app.on_event("startup")
async def _startup() -> None:
    if settings.eager_load:
        await tts.ensure_loaded()


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
        "model_id": settings.model_id,
        "device": tts.device,
        "dtype": tts.dtype,
        "loaded": tts.is_loaded,
        "eager_load": settings.eager_load,
    }


@app.post("/tts")
async def tts_from_ui(
    ref_audio: UploadFile = File(...),
    text: str = Form(...),
    ref_text: str | None = Form(None),
    language: str = Form("Japanese"),
) -> Response:
    return await _synthesize(ref_audio, text, ref_text=ref_text, language=language)


@app.post("/api/tts")
async def tts_api(
    ref_audio: UploadFile = File(...),
    text: str = Form(...),
    ref_text: str | None = Form(None),
    language: str = Form("Japanese"),
) -> Response:
    return await _synthesize(ref_audio, text, ref_text=ref_text, language=language)


async def _synthesize(
    ref_audio: UploadFile,
    text: str,
    *,
    ref_text: str | None,
    language: str,
) -> Response:
    suffix = Path(ref_audio.filename or "ref.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(await ref_audio.read())

    try:
        try:
            generated = await tts.synthesize_voice_clone(
                ref_audio_path=tmp_path,
                text=text,
                language=language,
                ref_text=ref_text,
            )
        except Exception as e:
            logger.exception("TTS failed")
            raise HTTPException(status_code=500, detail=str(e)) from e

        with tempfile.SpooledTemporaryFile() as buf:
            sf.write(buf, generated.wav, generated.sample_rate, format="WAV")
            buf.seek(0)
            data = buf.read()
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass

    return Response(
        content=data,
        media_type="audio/wav",
        headers={"Content-Disposition": 'attachment; filename="tts.wav"'},
    )
