import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import FileTooLargeError, InvalidAudioFormatError


SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(filename: str) -> str:
    name = Path(filename or "upload").name
    name = SAFE_NAME_RE.sub("_", name).strip("._")
    return name or "upload"


def validate_extension(filename: str, settings: Settings) -> str:
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in settings.allowed_extensions:
        raise InvalidAudioFormatError("Unsupported audio format")
    return extension


def validate_mime_type(content_type: str | None, settings: Settings) -> None:
    if content_type and content_type not in settings.allowed_mime_types:
        raise InvalidAudioFormatError("Unsupported audio MIME type")


async def store_upload(upload: UploadFile, settings: Settings) -> Path:
    validate_extension(upload.filename or "", settings)
    validate_mime_type(upload.content_type, settings)
    filename = f"{uuid4().hex}_{safe_filename(upload.filename or 'upload')}"
    target_path = (settings.uploads_dir / filename).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with target_path.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > settings.max_upload_bytes:
                target_path.unlink(missing_ok=True)
                raise FileTooLargeError("Uploaded file exceeds the MVP size limit")
            output.write(chunk)
    return target_path
