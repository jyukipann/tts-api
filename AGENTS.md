<INSTRUCTIONS>
## このレポの目的（現状コンテキスト）
- Mac（Apple Silicon）前提で **MPS** を使い、Hugging Face から取得する **Qwen3-TTS の voice clone** をローカル実行する。
- **FastAPI** で HTTP 経由の TTS API を提供し、簡単な **Web UI** からも使えるようにする。
- ストリーミング再生は不要。生成物は **WAV ダウンロード**。
- GitHub 個人アカウントの **Private repo**（ライセンスファイル無し）。

## 実装済み
- FastAPI アプリ: `src/tts_api/app.py`
  - `GET /` : Web UI（参照音声+テキスト送信 → wav ダウンロード）
  - `POST /tts` : Web UI 用（`multipart/form-data`）
  - `POST /api/tts` : API 用（`multipart/form-data`）
  - `GET /health` : ヘルスチェック
- モデルラッパ: `src/tts_api/model.py`
  - `qwen-tts` の `Qwen3TTSModel` を `from_pretrained()` で読み込み
  - `create_voice_clone_prompt` / `generate_voice_clone` を使って音声生成
  - デバイスは既定で `mps` 自動選択（無ければ `cpu`）
- 設定: `src/tts_api/settings.py`
  - `TTS_MODEL_ID`（既定: `Qwen/Qwen3-TTS-12Hz-0.6B-Base`）
  - `TTS_DEVICE`（例: `mps` / `cpu`）
  - `TTS_DTYPE`（既定: `float16`）
- Web テンプレ: `src/tts_api/templates/index.html`
- `uv` で依存管理: `pyproject.toml`

## 起動手順（開発）
```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
uv run uvicorn tts_api.app:app --host 127.0.0.1 --port 8000
```

## API 仕様（要点）
- `POST /api/tts`（`multipart/form-data`）
  - `ref_audio`: 参照音声ファイル
  - `text`: 生成したいテキスト（日本語優先）
  - `ref_text`（任意）: 参照音声の文字起こし
  - `language`（任意）: 既定 `Japanese`
- レスポンス: `audio/wav`（`Content-Disposition: attachment; filename="tts.wav"`）

## 注意事項 / 既知のリスク
- MPS は dtype/演算の相性で不安定になることがあるため、問題があれば `TTS_DTYPE=float32` や `TTS_DEVICE=cpu` を試す。
- 参照音声フォーマットは `audio/*` を許可しているが、まずは `wav` での利用を推奨。

## 今後のTODO（必要に応じて）
- 参照音声の長さ/サンプルレート/チャンネルを正規化する前処理。
- 生成パラメータ（速度/ピッチ/温度等）がモデル側で提供されていれば API に露出。
- 例外時のエラーレスポンス整備（詳細メッセージ/ログ）。
</INSTRUCTIONS>

