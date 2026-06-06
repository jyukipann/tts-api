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
        import mlx.core as mx
        import mlx_whisper
        import soundfile as sf

        # mlx_whisper 0.4.3 + mlx 0.31.x の互換性バグ修正:
        # stft() が list を as_strided に渡すが 0.31 は tuple を要求する
        _orig_as_strided = mx.as_strided

        def _patched_as_strided(a, shape=None, strides=None, offset=0, **kwargs):
            shape = tuple(shape) if isinstance(shape, list) else shape
            strides = tuple(strides) if isinstance(strides, list) else strides
            # MLX 0.31+ では位置引数で渡す必要がある
            return _orig_as_strided(a, shape, strides, offset, **kwargs)

        mx.as_strided = _patched_as_strided

        # soundfile で numpy array に変換して渡す（ffmpeg 依存を回避）
        # normalize_to_wav が 16kHz/16bit WAV を保証しているので resample 不要
        audio_array, _ = sf.read(str(audio_path), dtype="float32", always_2d=False)

        result: dict = await asyncio.to_thread(
            mlx_whisper.transcribe,
            audio_array,
            path_or_hf_repo=self._settings.stt_model_id,
            verbose=False,
        )
        return {
            "text": result["text"].strip(),
            "language": result.get("language", ""),
        }
