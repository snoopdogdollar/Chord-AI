from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import InvalidAnalysisRangeError, SongNotFoundError
from app.repositories import AnalysisRepository, JobRepository, SongRepository
from app.services.storage import store_upload
from app.services.youtube import validate_youtube_url


MIN_ANALYSIS_RANGE_SECONDS = 1.0


def validate_analysis_range(
    analysis_start_seconds: float | None,
    analysis_end_seconds: float | None,
) -> tuple[float | None, float | None]:
    if analysis_start_seconds is None and analysis_end_seconds is None:
        return None, None

    if analysis_start_seconds is None or analysis_end_seconds is None:
        raise InvalidAnalysisRangeError("Analysis range requires both start and end seconds")

    if analysis_start_seconds < 0:
        raise InvalidAnalysisRangeError("Analysis range start must be greater than or equal to 0")

    if analysis_end_seconds <= analysis_start_seconds:
        raise InvalidAnalysisRangeError("Analysis range end must be greater than start")

    if analysis_end_seconds - analysis_start_seconds < MIN_ANALYSIS_RANGE_SECONDS:
        raise InvalidAnalysisRangeError("Analysis range must be at least 1 second long")

    return analysis_start_seconds, analysis_end_seconds


class SongService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.songs = SongRepository(db)
        self.jobs = JobRepository(db)
        self.analysis = AnalysisRepository(db)

    async def create_from_upload(
        self,
        upload: UploadFile,
        analysis_start_seconds: float | None = None,
        analysis_end_seconds: float | None = None,
    ) -> tuple[str, str]:
        analysis_start_seconds, analysis_end_seconds = validate_analysis_range(
            analysis_start_seconds,
            analysis_end_seconds,
        )
        path = await store_upload(upload, self.settings)
        song = self.songs.create(
            title=Path(upload.filename or path.name).stem,
            source_type="upload",
            source_url=None,
            original_path=str(path),
            analysis_start_seconds=analysis_start_seconds,
            analysis_end_seconds=analysis_end_seconds,
        )
        job = self.jobs.create(song.id)
        return song.id, job.id

    def create_from_youtube(self, url: str) -> tuple[str, str]:
        validate_youtube_url(url)
        song = self.songs.create(title="YouTube Song", source_type="youtube", source_url=url, original_path=None)
        job = self.jobs.create(song.id)
        return song.id, job.id

    def get_song_payload(self, song_id: str) -> dict:
        song = self.songs.get(song_id)
        if not song:
            raise SongNotFoundError("Song was not found")
        job = self.jobs.latest_for_song(song_id)
        return {
            "song_id": song.id,
            "title": song.title,
            "duration": song.duration,
            "bpm": song.bpm,
            "key": None,
            "status": job.status if job else "unknown",
        }

    def get_chords_payload(self, song_id: str) -> dict:
        if not self.songs.get(song_id):
            raise SongNotFoundError("Song was not found")
        chords = self.analysis.list_chords(song_id)
        return {
            "song_id": song_id,
            "chords": [
                {
                    "start": chord.timestamp_start,
                    "end": chord.timestamp_end,
                    "chord": chord.chord_name,
                    "confidence": chord.confidence,
                }
                for chord in chords
            ],
        }

    def get_sheet_payload(self, song_id: str) -> dict:
        song = self.songs.get(song_id)
        if not song:
            raise SongNotFoundError("Song was not found")
        sheet = self.analysis.latest_sheet(song_id)
        content = sheet.content if sheet else ""
        return {
            "song_id": song_id,
            "sections": [{"name": "Song", "content": content.splitlines()}],
        }
