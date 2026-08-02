from pathlib import Path

from app.audio.beats import detect_beats
from app.audio.extraction import convert_to_wav
from app.audio.features import extract_chroma_features
from app.audio.models import BeatMap, FeatureSet
from app.audio.normalization import normalize_audio
from app.core.config import Settings


class AudioPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings

    def run(
        self,
        source_path: Path,
        song_id: str,
        *,
        analysis_start_seconds: float | None = None,
        analysis_end_seconds: float | None = None,
    ) -> tuple[Path, FeatureSet, BeatMap]:
        work_dir = self.settings.processed_dir / song_id
        extracted_path = convert_to_wav(
            source_path,
            work_dir / "input.wav",
            self.settings,
            analysis_start_seconds=analysis_start_seconds,
            analysis_end_seconds=analysis_end_seconds,
        )
        normalized_path = normalize_audio(extracted_path, work_dir / "normalized.wav", self.settings)
        features = extract_chroma_features(normalized_path, self.settings)
        beats = detect_beats(normalized_path, self.settings)
        return normalized_path, features, beats
