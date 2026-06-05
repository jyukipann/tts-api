from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TTS_", env_file=".env", extra="ignore")

    # TTS
    model_id: str = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
    device: str | None = None
    dtype: str = "float32"
    eager_load: bool = False

    # STT
    stt_model_id: str = "mlx-community/whisper-large-v3-turbo"
    stt_eager_load: bool = False
