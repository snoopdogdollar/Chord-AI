import subprocess
from pathlib import Path

from app.core.config import Settings
from app.core.errors import ProcessingFailedError


def normalize_audio(source_path: Path, target_path: Path, settings: Settings) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11,silenceremove=start_periods=1:start_duration=0.25:start_threshold=-45dB",
        "-ac",
        "1",
        "-ar",
        str(settings.internal_sample_rate),
        "-sample_fmt",
        "s16",
        str(target_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise ProcessingFailedError("ffmpeg is required for audio normalization") from exc
    except subprocess.CalledProcessError as exc:
        raise ProcessingFailedError(f"Audio normalization failed: {exc.stderr[-300:]}") from exc
    return target_path
