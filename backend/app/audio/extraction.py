import shutil
import subprocess
from pathlib import Path

from app.core.config import Settings
from app.core.errors import ProcessingFailedError


def convert_to_wav(source_path: Path, target_path: Path, settings: Settings) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.suffix.lower() == ".wav":
        shutil.copyfile(source_path, target_path)
        return target_path

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
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
        raise ProcessingFailedError("ffmpeg is required for audio conversion") from exc
    except subprocess.CalledProcessError as exc:
        raise ProcessingFailedError(f"Audio conversion failed: {exc.stderr[-300:]}") from exc
    return target_path
