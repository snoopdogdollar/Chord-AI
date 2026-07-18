from pathlib import Path

from app.audio.models import BeatMap
from app.core.config import Settings
from app.core.errors import ProcessingFailedError


def detect_beats(audio_path: Path, settings: Settings) -> BeatMap:
    try:
        import librosa
    except ImportError as exc:
        raise ProcessingFailedError("librosa is required for beat detection") from exc

    y, sample_rate = librosa.load(str(audio_path), sr=settings.internal_sample_rate, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sample_rate)
    beats = librosa.frames_to_time(beat_frames, sr=sample_rate)
    bpm = float(tempo[0] if hasattr(tempo, "__len__") else tempo)
    return BeatMap(bpm=bpm if bpm > 0 else None, beats=[float(value) for value in beats])
