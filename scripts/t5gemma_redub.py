#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None):
    print("+ " + " ".join(str(x) for x in cmd))
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {proc.returncode}: {' '.join(str(x) for x in cmd)}")
    return proc


def require_path(path, label):
    path = Path(path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path.resolve()


def require_command(name):
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command not found on PATH: {name}")


def load_dotenv_token(repo_root):
    env_path = repo_root / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.match(r"^\s*HF_TOKEN\s*=\s*(.+?)\s*$", line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return None


def ffprobe_duration(path):
    proc = run([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        str(path),
    ])
    return float(proc.stdout.strip())


def safe_file_part(value):
    value = re.sub(r'[\\/:*?"<>|]', "_", str(value or "line")).strip()
    return value or "line"


def load_lines(lines_json):
    data = json.loads(lines_json.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]
    if not isinstance(data, list) or not data:
        raise ValueError("Lines JSON must be a non-empty array, or an object with a non-empty 'segments' array.")
    return data


def resolve_lines(lines, base_dir):
    resolved = []
    for index, line in enumerate(lines):
        for key in ("id", "start", "end", "text", "reference_speech"):
            if key not in line:
                raise ValueError(f"Line index {index} is missing required property: {key}")

        start = float(line["start"])
        end = float(line["end"])
        if end <= start:
            raise ValueError(f"Line '{line['id']}' must have end greater than start.")
        duration = float(line.get("duration", end - start))
        if duration <= 0:
            raise ValueError(f"Line '{line['id']}' must have positive duration.")

        ref = Path(str(line["reference_speech"])).expanduser()
        if not ref.is_absolute():
            ref = base_dir / ref
        ref = require_path(ref, f"reference_speech for {line['id']}")

        speaker = str(line.get("speaker") or "speaker")
        file_name = line.get("file") or f"line_{index + 1:02d}_{safe_file_part(speaker)}.wav"

        resolved.append({
            "id": str(line["id"]),
            "speaker": speaker,
            "start": start,
            "end": end,
            "duration": duration,
            "text": str(line["text"]),
            "tts_text": str(line.get("tts_text") or line["text"]),
            "reference_speech": str(ref),
            "reference_text": line.get("reference_text"),
            "file": str(file_name),
        })
    return resolved


def copy_first_json(src_dir, dest):
    json_files = sorted(src_dir.glob("*.json"))
    if json_files:
        shutil.copy2(json_files[0], dest)


def main():
    parser = argparse.ArgumentParser(description="Whisper segment + T5Gemma-TTS voice-clone redub workflow.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--input-video", required=True)
    parser.add_argument("--lines-json", required=True)
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--t5gemma-root", default=os.environ.get("T5GEMMA_ROOT", "T5Gemma-TTS"))
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--model-dir", default="Aratako/T5Gemma-TTS-2b-2b")
    parser.add_argument("--whisper-model", default="small")
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--audio-bitrate", default="192k")
    parser.add_argument("--skip-normalize-audio", action="store_true")
    parser.add_argument("--normalize-integrated-lufs", type=float, default=-16.0)
    parser.add_argument("--normalize-true-peak", type=float, default=-1.5)
    parser.add_argument("--normalize-lra", type=float, default=11.0)
    parser.add_argument("--whisper-check-final", action="store_true")
    args = parser.parse_args()

    project_root = require_path(args.project_root, "project-root")
    input_video = require_path(args.input_video, "input-video")
    lines_json = require_path(args.lines_json, "lines-json")
    t5gemma_root = require_path(args.t5gemma_root, "t5gemma-root")
    python_exe = require_path(args.python_exe, "python-exe")
    inference_script = require_path(t5gemma_root / "run_inference_patched.py", "run_inference_patched.py")

    for command in ("ffmpeg", "ffprobe", "whisper"):
        require_command(command)

    repo_root = Path.cwd().resolve()
    if not os.environ.get("HF_TOKEN"):
        token = load_dotenv_token(repo_root)
        if token:
            os.environ["HF_TOKEN"] = token
    if not os.environ.get("HF_TOKEN"):
        raise RuntimeError("HF_TOKEN is not set. Set it in the environment or repository-root .env.")

    work_dir = project_root / "generated-video" / args.output_name
    delivery_dir = project_root / "video" / args.output_name
    whisper_dir = work_dir / "whisper"
    line_root = work_dir / "lines"
    final_whisper_dir = work_dir / "final_whisper_check"
    for directory in (work_dir, delivery_dir, whisper_dir, line_root):
        directory.mkdir(parents=True, exist_ok=True)

    video_duration = ffprobe_duration(input_video)
    lines = resolve_lines(load_lines(lines_json), lines_json.parent)
    resolved_json = work_dir / "lines_resolved.json"
    resolved_json.write_text(json.dumps(lines, ensure_ascii=False, indent=2), encoding="utf-8")

    run([
        "whisper",
        str(input_video),
        "--language",
        "Japanese",
        "--task",
        "transcribe",
        "--model",
        args.whisper_model,
        "--output_format",
        "json",
        "--output_dir",
        str(whisper_dir),
    ])

    for line in lines:
        output_dir = line_root / line["id"]
        output_dir.mkdir(parents=True, exist_ok=True)
        tts_cmd = [
            str(python_exe),
            str(inference_script),
            "--model_dir",
            args.model_dir,
            "--reference_speech",
            line["reference_speech"],
            "--target_text",
            line["tts_text"],
            "--target_duration",
            str(line["duration"]),
            "--output_dir",
            str(output_dir),
        ]
        if line.get("reference_text"):
            tts_cmd += ["--reference_text", str(line["reference_text"])]
        run(tts_cmd, cwd=t5gemma_root)
        generated = output_dir / "generated.wav"
        if not generated.exists():
            raise FileNotFoundError(f"T5Gemma-TTS did not produce {generated}")
        shutil.copy2(generated, work_dir / line["file"])

    inputs = []
    filters = []
    mix_inputs = []
    for index, line in enumerate(lines):
        audio_path = work_dir / line["file"]
        delay_ms = round(float(line["start"]) * 1000)
        inputs += ["-i", str(audio_path)]
        filters.append(
            f"[{index}:a]atrim=0:{line['duration']},asetpts=PTS-STARTPTS,adelay={delay_ms}|{delay_ms}[a{index}]"
        )
        mix_inputs.append(f"[a{index}]")

    raw_mixed = work_dir / "mixed_audio_raw.wav"
    mixed = work_dir / "mixed_audio.wav"
    filter_complex = ";".join(filters) + ";" + "".join(mix_inputs) + (
        f"amix=inputs={len(lines)}:normalize=0,apad,atrim=0:{video_duration}"
    )
    run(["ffmpeg", "-y", *inputs, "-filter_complex", filter_complex, "-ar", str(args.sample_rate), "-ac", "1", str(raw_mixed)])

    if args.skip_normalize_audio:
        shutil.copy2(raw_mixed, mixed)
    else:
        loudnorm = (
            f"loudnorm=I={args.normalize_integrated_lufs}:"
            f"TP={args.normalize_true_peak}:LRA={args.normalize_lra}"
        )
        run(["ffmpeg", "-y", "-i", str(raw_mixed), "-af", loudnorm, "-ar", str(args.sample_rate), "-ac", "1", str(mixed)])

    final_video = work_dir / f"{args.output_name}.mp4"
    run([
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-i",
        str(mixed),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        args.audio_bitrate,
        "-shortest",
        str(final_video),
    ])

    shutil.copy2(resolved_json, delivery_dir / "lines_resolved.json")
    shutil.copy2(raw_mixed, delivery_dir / "mixed_audio_raw.wav")
    shutil.copy2(mixed, delivery_dir / "mixed_audio.wav")
    shutil.copy2(final_video, delivery_dir / final_video.name)
    copy_first_json(whisper_dir, delivery_dir / "whisper_segments.json")
    for line in lines:
        shutil.copy2(work_dir / line["file"], delivery_dir / line["file"])

    if args.whisper_check_final:
        final_whisper_dir.mkdir(parents=True, exist_ok=True)
        run([
            "whisper",
            str(final_video),
            "--language",
            "Japanese",
            "--task",
            "transcribe",
            "--model",
            args.whisper_model,
            "--output_format",
            "json",
            "--output_dir",
            str(final_whisper_dir),
        ])
        copy_first_json(final_whisper_dir, delivery_dir / "final_whisper_check.json")

    mixed_duration = ffprobe_duration(mixed)
    final_duration = ffprobe_duration(final_video)
    streams = json.loads(run([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,channels,sample_rate,width,height",
        "-of",
        "json",
        str(final_video),
    ]).stdout)["streams"]
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    if len(video_streams) != 1 or len(audio_streams) != 1:
        raise RuntimeError(f"Expected one video and one audio stream; got video={len(video_streams)} audio={len(audio_streams)}")

    summary = {
        "ok": True,
        "project_root": str(project_root),
        "work_dir": str(work_dir.resolve()),
        "delivery_dir": str(delivery_dir.resolve()),
        "final_video": str((delivery_dir / final_video.name).resolve()),
        "mixed_audio_raw": str((delivery_dir / "mixed_audio_raw.wav").resolve()),
        "mixed_audio": str((delivery_dir / "mixed_audio.wav").resolve()),
        "normalized_audio": not args.skip_normalize_audio,
        "source_duration": video_duration,
        "mixed_audio_duration": mixed_duration,
        "final_video_duration": final_duration,
        "video_streams": len(video_streams),
        "audio_streams": len(audio_streams),
        "line_count": len(lines),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
