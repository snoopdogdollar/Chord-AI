from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioMetadata:
    path: Path
    sample_rate: int
    duration: float


@dataclass(frozen=True)
class FeatureSet:
    chroma: list[list[float]]
    timestamps: list[float]
    sample_rate: int
    hop_length: int
    duration: float


@dataclass(frozen=True)
class BeatMap:
    bpm: float | None
    beats: list[float]
