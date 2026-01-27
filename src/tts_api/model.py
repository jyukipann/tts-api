from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Literal

import numpy as np

from tts_api.settings import Settings


DeviceLiteral = Literal["mps", "cpu"]


@dataclass(frozen=True)
class GeneratedAudio:
    wav: np.ndarray
    sample_rate: int


class TTSService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = asyncio.Lock()
        self._model = None
        self._device: DeviceLiteral | None = None
        self._dtype_name: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def device(self) -> DeviceLiteral | None:
        return self._device

    @property
    def dtype(self) -> str | None:
        return self._dtype_name

    def load(self, *, dtype_name_override: str | None = None) -> None:
        import torch
        from qwen_tts import Qwen3TTSModel

        if self._model is not None:
            return

        if self._settings.device:
            device: DeviceLiteral = "mps" if self._settings.device.lower() == "mps" else "cpu"
        else:
            device = "mps" if torch.backends.mps.is_available() else "cpu"

        dtype_name = (dtype_name_override or self._settings.dtype or "float16").lower()
        dtype = {
            "float16": torch.float16,
            "float32": torch.float32,
            "bfloat16": torch.bfloat16,
        }.get(dtype_name, torch.float16)

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

        try:
            self._model = Qwen3TTSModel.from_pretrained(
                self._settings.model_id,
                device_map=device,
                dtype=dtype,
            )
        except TypeError:
            self._model = Qwen3TTSModel.from_pretrained(self._settings.model_id, dtype=dtype)
            _maybe_to_device(self._model, device)
        except Exception:
            self._model = Qwen3TTSModel.from_pretrained(self._settings.model_id)
            _maybe_to_device(self._model, device)

        self._device = device
        self._dtype_name = dtype_name

    def reload(self, *, dtype_name: str) -> None:
        self._model = None
        self._device = None
        self._dtype_name = None
        self.load(dtype_name_override=dtype_name)

    async def ensure_loaded(self) -> None:
        if self._model is not None:
            return
        async with self._lock:
            if self._model is not None:
                return
            await asyncio.to_thread(self.load)

    async def synthesize_voice_clone(
        self,
        *,
        ref_audio_path: str,
        text: str,
        language: str = "Japanese",
        ref_text: str | None = None,
    ) -> GeneratedAudio:
        await self.ensure_loaded()

        async with self._lock:
            try:
                return await asyncio.to_thread(
                    _generate_voice_clone,
                    self._model,
                    ref_audio_path,
                    text,
                    language,
                    (ref_text or "").strip(),
                )
            except RuntimeError as e:
                msg = str(e)
                is_prob_nan = "probability tensor contains" in msg or "nan" in msg.lower()
                if self._device == "mps" and (self._dtype_name or "").lower() == "float16" and is_prob_nan:
                    # MPS+fp16 can be numerically unstable on some prompts; retry with fp32.
                    self.reload(dtype_name="float32")
                    return await asyncio.to_thread(
                        _generate_voice_clone,
                        self._model,
                        ref_audio_path,
                        text,
                        language,
                        (ref_text or "").strip(),
                    )
                raise


def _maybe_to_device(model: object, device: DeviceLiteral) -> None:
    to = getattr(model, "to", None)
    if callable(to):
        try:
            to(device)  # type: ignore[misc]
            return
        except Exception:
            pass

    inner = getattr(model, "model", None)
    inner_to = getattr(inner, "to", None) if inner is not None else None
    if callable(inner_to):
        try:
            inner_to(device)  # type: ignore[misc]
        except Exception:
            pass


def _generate_voice_clone(
    model: object,
    ref_audio_path: str,
    text: str,
    language: str,
    ref_text: str,
) -> GeneratedAudio:
    if model is None:
        raise RuntimeError("Model not loaded.")
    create_prompt = getattr(model, "create_voice_clone_prompt", None)
    generate = getattr(model, "generate_voice_clone", None)
    if not callable(create_prompt) or not callable(generate):
        raise RuntimeError("Loaded model does not expose voice-clone APIs.")

    x_vector_only_mode = not bool(ref_text)
    prompt = create_prompt(
        ref_audio=ref_audio_path,
        ref_text=ref_text,
        x_vector_only_mode=x_vector_only_mode,
    )
    wavs, sample_rate = generate(
        text=text,
        voice_clone_prompt=prompt,
        language=language,
        non_streaming_mode=True,
    )
    if not wavs:
        raise RuntimeError("No audio generated.")
    wav = np.asarray(wavs[0])
    return GeneratedAudio(wav=wav, sample_rate=int(sample_rate))
