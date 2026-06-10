---
name: t5gemma-redub
description: Build and run portable Whisper segmentation plus T5Gemma-TTS voice-clone redubbing workflows. Use when Codex needs to set up T5Gemma-TTS on Windows, macOS, or Linux; create segment JSON from corrected dialogue and voice samples; generate duration-controlled speech; loudness-normalize audio; and replace a video's audio track.
---

# T5Gemma Redub

## Workflow

1. Read the project `README.md` first when working inside `project/<work-name>/`.
2. Keep project-specific inputs and outputs under that project:
   - voice samples: `assets/voice_sample/`
   - corrected segment JSON and helper scripts: `scripts/`
   - intermediates: `generated-video/<output-name>/`
   - final deliverables: `video/<output-name>/`
3. Use `scripts/t5gemma_redub.py` from this skill for cross-platform execution.
4. If the environment is not ready, read `references/setup.md` and install dependencies before running inference.
5. If segment JSON is missing, create it from the corrected script and Whisper timings. Use `references/lines-json.md` for the schema.

## Redub Command

Run from the repository or project workspace:

```bash
python /path/to/t5gemma-redub/scripts/t5gemma_redub.py \
  --project-root project/work-name \
  --input-video project/work-name/video/source.mp4 \
  --lines-json project/work-name/scripts/lines.json \
  --output-name t5gemma_redub_01 \
  --t5gemma-root /path/to/T5Gemma-TTS \
  --python-exe /path/to/t5gemma-python \
  --whisper-check-final
```

Prefer explicit paths. On Windows, use the patched inference script in the T5Gemma-TTS repo:
`run_inference_patched.py`.

## Segment JSON Rules

Each segment must include `id`, `start`, `end`, `text`, and `reference_speech`.

Use:
- `speaker` for readable filenames and reports.
- `reference_text` when the reference transcript is known.
- `tts_text` only for pronunciation guidance; keep the corrected display/script text in `text`.
- `duration` only when it should differ from `end - start`.

## Environment Rules

- Do not hardcode `HF_TOKEN` in scripts or repo files. Read it from the environment or a local `.env`.
- Ensure `ffmpeg`, `ffprobe`, and `whisper` are available on `PATH`.
- Use T5Gemma-TTS model `Aratako/T5Gemma-TTS-2b-2b` unless the user requests a different model.
- Use `--reference_speech`; do not use `--ref-wav`.
- Always pass `--target_duration` for segment-aligned redubbing.
- Keep the original T5Gemma line WAVs, raw mixed audio, normalized mixed audio, final MP4, resolved JSON, and Whisper outputs.

## Outputs

The bundled script writes:

- `generated-video/<output-name>/`: working files, raw line outputs, Whisper JSON, raw and normalized mix.
- `video/<output-name>/`: final deliverables copied for review.

By default, audio is normalized with ffmpeg `loudnorm` to `I=-16`, `TP=-1.5`, `LRA=11`. Use `--skip-normalize-audio` only when the user wants raw levels.

## References

- Read `references/setup.md` for Windows/macOS/Linux setup.
- Read `references/lines-json.md` for the segment JSON schema and example.
