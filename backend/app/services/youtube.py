import subprocess
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from app.core.config import Settings
from app.core.errors import InvalidYouTubeUrlError, YouTubeExtractionError


ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def validate_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme not in {"http", "https"} or host.lower() not in ALLOWED_HOSTS:
        raise InvalidYouTubeUrlError("URL is not a supported YouTube URL")
    return url


def download_youtube_audio(url: str, settings: Settings) -> Path:
    validate_youtube_url(url)
    output_template = settings.uploads_dir / f"{uuid4().hex}.%(ext)s"
    command = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format",
        "wav",
        "--output",
        str(output_template),
        url,
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
    except FileNotFoundError as exc:
        raise YouTubeExtractionError("yt-dlp is required for YouTube extraction") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace")
        stdout = (exc.stdout or b"").decode("utf-8", errors="replace")
        detail = (stderr or stdout or "no output")[-300:].strip()
        raise YouTubeExtractionError(f"Could not extract audio: {detail}") from exc

    candidates = sorted(settings.uploads_dir.glob(f"{output_template.stem}.*"))
    if not candidates:
        raise YouTubeExtractionError("YouTube extraction did not produce an audio file")
    return candidates[0]
