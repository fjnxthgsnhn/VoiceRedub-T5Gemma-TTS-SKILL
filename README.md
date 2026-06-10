# VoiceRedub T5Gemma-TTS Skill

Whisperで動画をセグメンテーションし、T5Gemma-TTSでボイスサンプル参照の音声を生成し、音量正規化した音声で元動画をリダブするCodex Skillです。Windows、macOS、Linuxで使えるように、実行本体はPythonスクリプトとして同梱しています。

## 構成

```text
VoiceRedub-T5Gemma-TTS-SKILL/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── lines-json.md
│   └── setup.md
└── scripts/
    └── t5gemma_redub.py
```

## できること

- 入力動画をWhisperで文字起こし・セグメンテーション
- 修正済みセリフJSONに基づくT5Gemma-TTS音声生成
- `reference_speech`によるボイスクローン
- `target_duration`によるセグメント尺合わせ
- ffmpeg `loudnorm`による音量正規化
- 元動画の映像を保持したまま音声のみ差し替え
- 個別音声、ミックス音声、最終MP4、Whisper確認結果をプロジェクト配下に保存

## 前提

- Python 3.10または3.11推奨
- `ffmpeg` / `ffprobe`
- `whisper`
- T5Gemma-TTSリポジトリ
- Hugging Face token: `HF_TOKEN`

詳細な環境構築は `references/setup.md` を参照してください。

## 実行例

```bash
python /path/to/VoiceRedub-T5Gemma-TTS-SKILL/scripts/t5gemma_redub.py \
  --project-root project/work-name \
  --input-video project/work-name/video/source.mp4 \
  --lines-json project/work-name/scripts/lines.json \
  --output-name t5gemma_redub_01 \
  --t5gemma-root /path/to/T5Gemma-TTS \
  --python-exe /path/to/python \
  --whisper-check-final
```

Windows例:

```powershell
$env:HF_TOKEN = "your_token_here"
python C:\Users\huge2\.codex\skills\VoiceRedub-T5Gemma-TTS-SKILL\scripts\t5gemma_redub.py `
  --project-root project\work-name `
  --input-video project\work-name\video\source.mp4 `
  --lines-json project\work-name\scripts\lines.json `
  --output-name t5gemma_redub_01 `
  --t5gemma-root H:\AICreation\T5Gemma-TTS `
  --python-exe C:\Users\huge2\.conda\envs\t5gemma-tts\python.exe `
  --whisper-check-final
```

## Lines JSON

`lines.json` は `project/<work-name>/scripts/` に置きます。

```json
[
  {
    "id": "rei_01",
    "speaker": "rei",
    "start": 0.0,
    "end": 2.4,
    "text": "熱いので、気をつけてくださいね",
    "reference_speech": "../assets/voice_sample/rei_ref.wav",
    "reference_text": "熱いので、気をつけてくださいね"
  },
  {
    "id": "regular_01",
    "speaker": "regular",
    "start": 2.4,
    "end": 4.26,
    "text": "玲ちゃん、今日もかわいいね",
    "tts_text": "れいちゃん、今日もかわいいね",
    "reference_speech": "../assets/voice_sample/regular_male_ref.wav",
    "reference_text": "玲ちゃん、今日もかわいいね"
  }
]
```

詳しいスキーマは `references/lines-json.md` を参照してください。

## 出力

作業ファイル:

```text
project/<work-name>/generated-video/<output-name>/
```

納品ファイル:

```text
project/<work-name>/video/<output-name>/
```

主な出力:

- 個別生成WAV
- `mixed_audio_raw.wav`
- `mixed_audio.wav`
- `<output-name>.mp4`
- `lines_resolved.json`
- `whisper_segments.json`
- `final_whisper_check.json`（`--whisper-check-final`指定時）

## 音量正規化

デフォルトではffmpeg `loudnorm` を使い、以下で正規化します。

- Integrated loudness: `-16 LUFS`
- True peak: `-1.5 dBTP`
- LRA: `11`

正規化しない場合:

```bash
--skip-normalize-audio
```

## 注意点

- 実際のHFトークンをREADMEやスクリプトに保存しないでください。
- `HF_TOKEN` は環境変数、または作業リポジトリ直下のローカル `.env` から読みます。
- T5Gemma-TTSでは `--reference_speech` を使います。`--ref-wav` ではありません。
- セグメント尺合わせが必要な場合は `target_duration` を必ず使います。
- 読み間違い補正は `text` を正規セリフとして残し、発音誘導だけ `tts_text` に書きます。
