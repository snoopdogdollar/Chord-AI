from app.audio.models import BeatMap, FeatureSet
from app.chords.classifier import classify_chroma
from app.chords.models import ChordEvent
from app.chords.smoothing import smooth_predictions


class ChordDetector:
    def detect(self, features: FeatureSet, beat_map: BeatMap) -> list[ChordEvent]:
        labels: list[str] = []
        confidences: list[float] = []
        for chroma_vector in features.chroma:
            label, confidence = classify_chroma(chroma_vector)
            labels.append(label)
            confidences.append(confidence)
        return smooth_predictions(labels, confidences, features.timestamps, features.duration, beat_map)
