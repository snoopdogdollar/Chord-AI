from sqlalchemy.orm import Session

from app.db.models import (
    ChordProgression,
    GeneratedExport,
    GeneratedSheet,
    JobStatus,
    ProcessingJob,
    Song,
)


class SongRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, title: str, source_type: str, source_url: str | None, original_path: str | None) -> Song:
        song = Song(title=title, source_type=source_type, source_url=source_url, original_path=original_path)
        self.db.add(song)
        self.db.commit()
        self.db.refresh(song)
        return song

    def get(self, song_id: str) -> Song | None:
        return self.db.get(Song, song_id)

    def update_analysis(self, song: Song, *, processed_path: str, duration: float | None, bpm: float | None) -> Song:
        song.processed_path = processed_path
        song.duration = duration
        song.bpm = bpm
        self.db.commit()
        self.db.refresh(song)
        return song


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, song_id: str) -> ProcessingJob:
        job = ProcessingJob(song_id=song_id)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get(self, job_id: str) -> ProcessingJob | None:
        return self.db.get(ProcessingJob, job_id)

    def latest_for_song(self, song_id: str) -> ProcessingJob | None:
        return (
            self.db.query(ProcessingJob)
            .filter(ProcessingJob.song_id == song_id)
            .order_by(ProcessingJob.created_at.desc())
            .first()
        )

    def mark_processing(self, job: ProcessingJob, *, stage: str, progress: int) -> ProcessingJob:
        job.status = JobStatus.processing.value
        job.stage = stage
        job.progress = progress
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_completed(self, job: ProcessingJob) -> ProcessingJob:
        job.status = JobStatus.completed.value
        job.stage = None
        job.progress = 100
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_failed(self, job: ProcessingJob, *, code: str, message: str) -> ProcessingJob:
        job.status = JobStatus.failed.value
        job.error_code = code
        job.error_message = message
        self.db.commit()
        self.db.refresh(job)
        return job


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def replace_chords(self, song_id: str, chords: list[dict]) -> None:
        self.db.query(ChordProgression).filter(ChordProgression.song_id == song_id).delete()
        for chord in chords:
            self.db.add(
                ChordProgression(
                    song_id=song_id,
                    timestamp_start=chord["start"],
                    timestamp_end=chord["end"],
                    chord_name=chord["chord"],
                    confidence=chord["confidence"],
                )
            )
        self.db.commit()

    def list_chords(self, song_id: str) -> list[ChordProgression]:
        return (
            self.db.query(ChordProgression)
            .filter(ChordProgression.song_id == song_id)
            .order_by(ChordProgression.timestamp_start.asc())
            .all()
        )

    def create_sheet(self, song_id: str, content: str) -> GeneratedSheet:
        sheet = GeneratedSheet(song_id=song_id, content=content)
        self.db.add(sheet)
        self.db.commit()
        self.db.refresh(sheet)
        return sheet

    def latest_sheet(self, song_id: str) -> GeneratedSheet | None:
        return (
            self.db.query(GeneratedSheet)
            .filter(GeneratedSheet.song_id == song_id)
            .order_by(GeneratedSheet.created_at.desc())
            .first()
        )

    def create_export(self, song_id: str, export_format: str, file_path: str) -> GeneratedExport:
        export = GeneratedExport(song_id=song_id, export_format=export_format, file_path=file_path)
        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)
        return export

    def get_export(self, export_id: str) -> GeneratedExport | None:
        return self.db.get(GeneratedExport, export_id)
