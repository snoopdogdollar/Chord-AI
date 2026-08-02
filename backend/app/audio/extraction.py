import shutil
import subprocess
from pathlib import Path

from app.core.config import Settings
from app.core.errors import ProcessingFailedError


def convert_to_wav(
    source_path: Path,
    target_path: Path,
    settings: Settings,
    *,
    analysis_start_seconds: float | None = None,
    analysis_end_seconds: float | None = None,
) -> Path:
    """Convert *source_path* to a mono 16-bit WAV at the configured sample rate.

    When *analysis_start_seconds* and *analysis_end_seconds* are both provided
    the output is trimmed to that segment using ffmpeg's -ss / -t flags, so
    every downstream step (normalization, features, beats) sees only the
    requested slice of audio.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)

    has_range = analysis_start_seconds is not None and analysis_end_seconds is not None

    # Fast-path for .wav files that need no range trimming.
    if source_path.suffix.lower() == ".wav" and not has_range:
        shutil.copyfile(source_path, target_path)
        return target_path

    command = ["ffmpeg", "-y"]

    if has_range:
        # Seek before -i for fast, accurate segment extraction.
        command += ["-ss", str(analysis_start_seconds)]

    command += ["-i", str(source_path)]

    if has_range:
        duration = analysis_end_seconds - analysis_start_seconds  # type: ignore[operator]
        command += ["-t", str(duration)]

    command += [
        "-ac", "1",
        "-ar", str(settings.internal_sample_rate),
        "-sample_fmt", "s16",
        str(target_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True)
    except FileNotFoundError as exc:
        raise ProcessingFailedError("ffmpeg is required for audio conversion") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace")
        stdout = (exc.stdout or b"").decode("utf-8", errors="replace")
        detail = (stderr or stdout or "no output")[-500:].strip()
        raise ProcessingFailedError(f"Audio conversion failed: {detail}") from exc
    return target_path
