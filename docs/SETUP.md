# セットアップ（macOS / Apple Silicon）

このプロジェクトは **Mac 専用**で、PyTorch の **MPS** を使って Qwen3-TTS voice clone を動かします。

## 必要なもの

- macOS（Apple Silicon 推奨）
- `uv`
- Python 3.12

## 依存関係のセットアップ

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

## 推奨（任意）

音声処理で `sox` が使われるケースがあるため、警告が気になる場合は入れておくと楽です。

```bash
brew install sox
```

## 環境変数

`.env.example` を参考に `.env` を作れます。

- `TTS_MODEL_ID`（既定: `Qwen/Qwen3-TTS-12Hz-0.6B-Base`）
- `TTS_DEVICE`（例: `mps` / `cpu`）
- `TTS_DTYPE`（既定: `float32`）
- `TTS_EAGER_LOAD`（既定: `false`）

