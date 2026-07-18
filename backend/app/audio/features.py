from pathlib import Path

from app.audio.models import FeatureSet
from app.core.config import Settings
from app.core.errors import ProcessingFailedError


def extract_chroma_features(audio_path: Path, settings: Settings) -> FeatureSet:
    try:
        import librosa
        import numpy as np
    except ImportError as exc:
        raise ProcessingFailedError("librosa and numpy are required for feature extraction") from exc

    hop_length = 2048
    y, sample_rate = librosa.load(str(audio_path), sr=settings.internal_sample_rate, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sample_rate))
    if duration <= 0.05:
        raise ProcessingFailedError("Audio is empty or too short to analyze")
    if duration > settings.max_audio_duration_seconds:
        raise ProcessingFailedError("Audio duration exceeds the MVP limit")

    chroma = librosa.feature.chroma_cqt(y=y, sr=sample_rate, hop_length=hop_length)
    chroma = np.nan_to_num(chroma, nan=0.0, posinf=0.0, neginf=0.0)
    timestamps = librosa.frames_to_time(range(chroma.shape[1]), sr=sample_rate, hop_length=hop_length)

    return FeatureSet(
        chroma=chroma.T.astype(float).tolist(),
        timestamps=[float(value) for value in timestamps],
        sample_rate=int(sample_rate),
        hop_length=hop_length,
        duration=duration,
    )
