# tts-api

Mac（MPS）で **Qwen3-TTS のボイスクローン**をローカル実行し、FastAPI 経由で `.wav` を返す API + 簡易 Web UI です。

想定モデルは Hugging Face の公式 `Qwen/Qwen3-TTS-12Hz-0.6B-Base`（日本語対応）です。

## 前提

- macOS（Apple Silicon 推奨）
- `uv`（Python パッケージ/環境管理）

## セットアップ

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

初回起動時に Hugging Face からモデルがダウンロードされます。
環境変数は `.env` でも指定できます（例は `.env.example`）。

## 起動

```bash
uv run uvicorn tts_api.app:app --host 127.0.0.1 --port 8000
```

- Web UI: `http://127.0.0.1:8000/`

## API

`POST /api/tts`（`multipart/form-data`）

- `ref_audio`: 参照音声ファイル（推奨: wav）
- `text`: 話させたいテキスト
- `ref_text`(optional): 参照音声の文字起こし（あると精度/安定性が上がることがあります）
- `language`(optional): 既定 `Japanese`

例:

```bash
curl -F "ref_audio=@voice.wav" -F "text=こんにちは。テストです。" http://127.0.0.1:8000/api/tts -o out.wav
```

## 設定（環境変数）

`TTS_` プレフィックスで設定できます（例: `TTS_MODEL_ID`）。

- `TTS_MODEL_ID`（既定: `Qwen/Qwen3-TTS-12Hz-0.6B-Base`）
- `TTS_DEVICE`（既定: 自動。MPS があれば `mps`）
- `TTS_DTYPE`（既定: `float16`）

## トラブルシュート

- MPS で落ちる/変な音になる場合: `TTS_DTYPE=float32` を試してください（遅くなります）。
- それでも難しい場合: `TTS_DEVICE=cpu` で動作確認してください。
