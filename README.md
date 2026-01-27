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

LAN に公開する場合:

```bash
HF_HOME="$PWD/.cache/huggingface" uv run uvicorn tts_api.app:app --host 0.0.0.0 --port 8010
```

macOS のファイアウォール許可が出たら許可してください。

モデルは既定で **初回リクエスト時に lazy-load** します。起動時にロードしたい場合は `TTS_EAGER_LOAD=true` を指定してください。

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
- `TTS_DTYPE`（既定: `float32`）
- `TTS_EAGER_LOAD`（既定: `false`）

## トラブルシュート

- 速度優先: `TTS_DTYPE=float16`（MPS で不安定になる場合があります）。
- 安定優先: `TTS_DTYPE=float32`（既定。遅くなります）。
- それでも難しい場合: `TTS_DEVICE=cpu` で動作確認してください。

参照音声について:

- まずは **短め（3〜15秒程度）** のクリアな音声（ノイズ/残響少なめ）から試すのがおすすめです。
- `ref_text`（参照音声の文字起こし）を入れると安定することがあります。

SoX の警告が出る場合:

- `brew install sox` で解消することがあります（モデル側の音声処理で使われる場合があります）。
