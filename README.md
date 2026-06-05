# tts-api

Mac（MPS）で **Qwen3-TTS のボイスクローン**をローカル実行し、FastAPI 経由で `.wav` を返す API + 簡易 Web UI。

- ポート: **8010**（LAN 公開）/ 8000（localhost のみ）
- モデル: `Qwen/Qwen3-TTS-12Hz-0.6B-Base`

## セットアップ

```bash
uv sync
cp .env.example .env  # 必要に応じて編集
```

初回リクエスト時に HuggingFace からモデルが自動ダウンロードされます。

---

## 手動起動

```bash
# localhost のみ
uv run uvicorn tts_api.app:app --host 127.0.0.1 --port 8000

# LAN 公開
HF_HOME="$PWD/.cache/huggingface" uv run uvicorn tts_api.app:app --host 0.0.0.0 --port 8010
```

Web UI: `http://127.0.0.1:8010/`

---

## サービス化（launchd）

ログイン時に自動起動するサービスとして登録する。

```bash
# 1. plist をインストール
cp scripts/com.jyukipann.tts-api.plist ~/Library/LaunchAgents/

# 2. 登録・起動
launchctl load ~/Library/LaunchAgents/com.jyukipann.tts-api.plist

# 3. 動作確認
curl http://localhost:8010/health
```

### サービス管理コマンド

```bash
# 停止
launchctl unload ~/Library/LaunchAgents/com.jyukipann.tts-api.plist

# 再起動
launchctl unload ~/Library/LaunchAgents/com.jyukipann.tts-api.plist
launchctl load   ~/Library/LaunchAgents/com.jyukipann.tts-api.plist

# ログ確認
tail -f server.log
```

> **plist のパスを変えた場合**は `WorkingDirectory` と `ProgramArguments` の `/Users/juki/Workspace/tts` を実際のパスに合わせて編集してください。

---

## CLI（curl）

### ボイスクローン

```bash
curl -s \
  -F "ref_audio=@voice.wav" \
  -F "text=こんにちは。テストです。" \
  http://localhost:8010/api/tts \
  -o output.wav
```

### ref_text を渡すと精度が上がることがある

```bash
curl -s \
  -F "ref_audio=@voice.wav" \
  -F "ref_text=参照音声の文字起こし" \
  -F "text=話させたいテキスト" \
  -F "language=Japanese" \
  http://localhost:8010/api/tts \
  -o output.wav
```

### ヘルスチェック

```bash
curl http://localhost:8010/health
```

---

## 環境変数（`TTS_` プレフィックス）

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `TTS_MODEL_ID` | `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | モデル |
| `TTS_DEVICE` | 自動（MPS → CPU） | `mps` / `cpu` |
| `TTS_DTYPE` | `float32` | `float32` / `float16` |
| `TTS_EAGER_LOAD` | `false` | 起動時ロード |

## トラブルシュート

- **速度優先**: `TTS_DTYPE=float16`（MPS で不安定になる場合あり）
- **安定優先**: `TTS_DTYPE=float32`（デフォルト）
- **動作確認**: `TTS_DEVICE=cpu`
- **SoX 警告**: `brew install sox` で解消
