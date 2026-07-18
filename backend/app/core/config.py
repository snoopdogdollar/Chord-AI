from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChordAI"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/chordai.sqlite3"
    storage_root: Path = Path("./data")
    max_upload_bytes: int = 100 * 1024 * 1024
    max_audio_duration_seconds: int = 15 * 60
    internal_sample_rate: int = 44100
    allowed_extensions: set[str] = {"mp3", "wav", "flac", "m4a"}
    allowed_mime_types: set[str] = {
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/flac",
        "audio/mp4",
        "audio/x-m4a",
    }
    allowed_export_formats: set[str] = {"txt", "pdf"}
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_prefix="CHORDAI_", env_file=".env")

    @property
    def uploads_dir(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def processed_dir(self) -> Path:
        return self.storage_root / "processed"

    @property
    def cache_dir(self) -> Path:
        return self.storage_root / "cache"

    @property
    def exports_dir(self) -> Path:
        return self.storage_root / "exports"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for directory in (
        settings.storage_root,
        settings.uploads_dir,
        settings.processed_dir,
        settings.cache_dir,
        settings.exports_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return settings
