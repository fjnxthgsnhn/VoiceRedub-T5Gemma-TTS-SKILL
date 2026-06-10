# Lines JSON

Create this file under `project/<work-name>/scripts/`.

## Required Fields

- `id`: stable segment id.
- `start`: start time in seconds.
- `end`: end time in seconds.
- `text`: corrected script text.
- `reference_speech`: voice sample WAV path. Relative paths are resolved from the JSON file's directory.

## Optional Fields

- `speaker`: used in filenames and reports.
- `duration`: target TTS duration in seconds. Defaults to `end - start`.
- `reference_text`: transcript of the reference voice sample. Prefer setting this when known.
- `tts_text`: pronunciation-guided text for TTS. Use this only when generation needs kana or wording hints; keep the corrected script in `text`.
- `file`: output WAV filename.

## Example

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

If relative paths are inconvenient, use absolute paths.
