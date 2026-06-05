"""STT サービス（mlx-whisper）。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from tts_api.settings import Settings


class STTService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._loaded = False
        self._lock = asyncio.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    async def ensure_loaded(self) -> None:
        if self._loaded:
            return
        async with self._lock:
            if self._loaded:
                return
            # mlx_whisper はモデルを初回呼び出し時に自動 DL するため、ここでは起動フラグのみ立てる
            self._loaded = True

    async def transcribe(self, audio_path: Path) -> dict[str, str]:
        """音声ファイルを文字起こしして {"text": ..., "language": ...} を返す。"""
        await self.ensure_loaded()
        import mlx_whisper

        result: dict = await asyncio.to_thread(
            mlx_whisper.transcribe,
            str(audio_path),
            path_or_hf_repo=self._settings.stt_model_id,
            verbose=False,
        )
        return {
            "text": result["text"].strip(),
            "language": result.get("language", ""),
        }
