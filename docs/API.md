# API

## エンドポイント

- `GET /` : Web UI
- `POST /tts` : Web UI 用（`multipart/form-data`、WAVを返す）
- `POST /api/tts` : API 用（`multipart/form-data`、WAVを返す）
- `GET /health` : ヘルス

## `POST /api/tts`

`multipart/form-data`

- `ref_audio`（必須）: 参照音声（推奨: wav）
- `text`（必須）: 話させたいテキスト
- `ref_text`（任意）: 参照音声の文字起こし（あると安定することがあります）
- `language`（任意）: 既定 `Japanese`

レスポンス:

- `Content-Type: audio/wav`
- `Content-Disposition: attachment; filename="tts.wav"`

例:

```bash
curl -F "ref_audio=@voice.wav" \
     -F "ref_text=（任意）参照音声の文字起こし" \
     -F "text=こんにちは。テストです。" \
     -F "language=Japanese" \
     http://127.0.0.1:8000/api/tts -o out.wav
```

エラー:

- 失敗時は `500` を返します（`detail` に例外メッセージが入ります）。

