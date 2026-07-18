from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SourceType(str, Enum):
    upload = "upload"
    youtube = "youtube"


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ProcessingStage(str, Enum):
    audio_extraction = "audio_extraction"
    normalization = "normalization"
    feature_extraction = "feature_extraction"
    beat_detection = "beat_detection"
    chord_detection = "chord_detection"
    sheet_generation = "sheet_generation"
    export_generation = "export_generation"


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("song"))
    title: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(20))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="song")
    chords: Mapped[list["ChordProgression"]] = relationship(back_populates="song", cascade="all, delete-orphan")
    sheets: Mapped[list["GeneratedSheet"]] = relationship(back_populates="song", cascade="all, delete-orphan")
    exports: Mapped[list["GeneratedExport"]] = relationship(back_populates="song", cascade="all, delete-orphan")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("job"))
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.queued.value)
    stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    song: Mapped[Song] = relationship(back_populates="jobs")


class ChordProgression(Base):
    __tablename__ = "chord_progressions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("chord"))
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)
    timestamp_start: Mapped[float] = mapped_column(Float)
    timestamp_end: Mapped[float] = mapped_column(Float)
    chord_name: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float)

    song: Mapped[Song] = relationship(back_populates="chords")


class GeneratedSheet(Base):
    __tablename__ = "generated_sheets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("sheet"))
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    song: Mapped[Song] = relationship(back_populates="sheets")


class GeneratedExport(Base):
    __tablename__ = "generated_exports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("export"))
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)
    export_format: Mapped[str] = mapped_column(String(8))
    file_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    song: Mapped[Song] = relationship(back_populates="exports")
