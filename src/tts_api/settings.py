from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TTS_", env_file=".env", extra="ignore")

    model_id: str = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
    device: str | None = None  # e.g. "mps", "cpu"
    dtype: str = "float16"  # "float16" | "float32" | "bfloat16"

