"""macOS ネイティブ（afconvert）を使った音声フォーマット変換ユーティリティ。"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

MIME_BY_FORMAT: dict[str, str] = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
}

SUPPORTED_INPUT = {".wav", ".mp3", ".m4a"}
SUPPORTED_OUTPUT = set(MIME_BY_FORMAT.keys())


def normalize_to_wav(src: Path) -> tuple[Path, bool]:
    """任意フォーマットの音声を WAV（16kHz/16bit）に変換して返す。

    Returns:
        (wav_path, is_temp) — is_temp=True の場合は呼び出し元で unlink すること。
    """
    if src.suffix.lower() == ".wav":
        return src, False
    tmp = Path(tempfile.mktemp(suffix=".wav"))
    subprocess.run(
        ["afconvert", str(src), "-o", str(tmp), "-d", "LEI16@16000", "-f", "WAVE"],
        check=True,
        capture_output=True,
    )
    return tmp, True


def wav_to_format(wav_path: Path, fmt: str) -> bytes:
    """WAV ファイルを指定フォーマットのバイト列に変換して返す。"""
    fmt = fmt.lower()
    if fmt not in SUPPORTED_OUTPUT:
        raise ValueError(f"Unsupported output format: {fmt}. Supported: {SUPPORTED_OUTPUT}")

    if fmt == "wav":
        return wav_path.read_bytes()

    tmp = Path(tempfile.mktemp(suffix=f".{fmt}"))
    try:
        if fmt == "m4a":
            subprocess.run(
                ["afconvert", str(wav_path), "-o", str(tmp), "-f", "m4af", "-d", "aac"],
                check=True,
                capture_output=True,
            )
        elif fmt == "mp3":
            subprocess.run(
                ["afconvert", str(wav_path), "-o", str(tmp), "-f", "MP3f", "-d", ".mp3"],
                check=True,
                capture_output=True,
            )
        return tmp.read_bytes()
    finally:
        tmp.unlink(missing_ok=True)
