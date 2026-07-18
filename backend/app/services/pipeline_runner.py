from pathlib import Path

from sqlalchemy.orm import Session

from app.audio.beats import detect_beats
from app.audio.extraction import convert_to_wav
from app.audio.features import extract_chroma_features
from app.audio.normalization import normalize_audio
from app.chords.detector import ChordDetector
from app.chords.models import ChordEvent
from app.core.config import Settings
from app.core.errors import ChordAIError, ProcessingFailedError, SongNotFoundError
from app.db.models import ProcessingStage
from app.repositories import AnalysisRepository, JobRepository, SongRepository
from app.services.youtube import download_youtube_audio
from app.sheets.generator import generate_sheet_text


class PipelineRunner:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.songs = SongRepository(db)
        self.jobs = JobRepository(db)
        self.analysis = AnalysisRepository(db)

    def run_job(self, job_id: str) -> None:
        job = self.jobs.get(job_id)
        if not job:
            return
        song = self.songs.get(job.song_id)
        if not song:
            self.jobs.mark_failed(job, code="SONG_NOT_FOUND", message="Song was not found")
            return

        try:
            if song.source_type == "youtube":
                if not song.source_url:
                    raise SongNotFoundError("Song has no YouTube source URL")
                self.jobs.mark_processing(job, stage=ProcessingStage.audio_extraction.value, progress=10)
                source_path = download_youtube_audio(song.source_url, self.settings)
                song.original_path = str(source_path)
                self.db.commit()
            elif song.original_path:
                source_path = Path(song.original_path)
            else:
                raise SongNotFoundError("Song has no source audio")

            self.jobs.mark_processing(job, stage=ProcessingStage.audio_extraction.value, progress=10)
            work_dir = self.settings.processed_dir / song.id
            extracted_path = convert_to_wav(source_path, work_dir / "input.wav", self.settings)

            self.jobs.mark_processing(job, stage=ProcessingStage.normalization.value, progress=25)
            processed_path = normalize_audio(extracted_path, work_dir / "normalized.wav", self.settings)

            self.jobs.mark_processing(job, stage=ProcessingStage.feature_extraction.value, progress=45)
            features = extract_chroma_features(processed_path, self.settings)

            self.jobs.mark_processing(job, stage=ProcessingStage.beat_detection.value, progress=60)
            beats = detect_beats(processed_path, self.settings)

            self.jobs.mark_processing(job, stage=ProcessingStage.chord_detection.value, progress=70)
            chord_events = ChordDetector().detect(features, beats)

            self.jobs.mark_processing(job, stage=ProcessingStage.sheet_generation.value, progress=85)
            content = generate_sheet_text(song.title, chord_events)

            self.songs.update_analysis(
                song,
                processed_path=str(processed_path),
                duration=features.duration,
                bpm=beats.bpm,
            )
            self.analysis.replace_chords(song.id, [event.to_dict() for event in chord_events])
            self.analysis.create_sheet(song.id, content)
            self.jobs.mark_completed(job)
        except ChordAIError as exc:
            self.jobs.mark_failed(job, code=exc.code, message=exc.message)
        except Exception as exc:
            self.jobs.mark_failed(job, code="PROCESSING_FAILED", message=str(exc) or "Processing failed")


def run_synthetic_analysis(title: str, chords: list[ChordEvent]) -> str:
    if not chords:
        raise ProcessingFailedError("No chords were detected")
    return generate_sheet_text(title, chords)
