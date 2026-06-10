# T5Gemma Redub Setup

Use these steps when the target environment does not already have T5Gemma-TTS ready.

## System Dependencies

Install `ffmpeg` so both `ffmpeg` and `ffprobe` are on `PATH`.

- Windows: use winget, Chocolatey, or a portable ffmpeg build.
- macOS: `brew install ffmpeg`
- Linux: use the system package manager, for example `sudo apt install ffmpeg`.

Install Python 3.10 or 3.11 for best compatibility with ML packages.

## T5Gemma-TTS Repository

Clone or copy T5Gemma-TTS:

```bash
git clone https://github.com/Aratako/T5Gemma-TTS.git
cd T5Gemma-TTS
```

On Windows, prefer `run_inference_patched.py` when present. If it is missing, use the repository's CLI inference script only after confirming SSL/Hugging Face downloads work.

## Python Environment

Create an isolated environment. Conda is recommended for CUDA setups:

```bash
conda create -n t5gemma-tts python=3.10 -y
conda activate t5gemma-tts
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For venv:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows venv activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Whisper

Install Whisper in the same environment or another environment available on `PATH`:

```bash
python -m pip install -U openai-whisper
```

## Hugging Face Token

Do not write real tokens into scripts or committed files. Set `HF_TOKEN` in the environment:

```bash
export HF_TOKEN="..."
```

PowerShell:

```powershell
$env:HF_TOKEN = "..."
```

The bundled script can also read `HF_TOKEN` from a local repository-root `.env`.

## Smoke Test

Before a full redub, verify:

```bash
ffmpeg -version
ffprobe -version
whisper --help
python /path/to/T5Gemma-TTS/run_inference_patched.py --help
```

The first model run may download several GB from Hugging Face.
