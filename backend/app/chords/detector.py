from app.audio.models import BeatMap, FeatureSet
from app.chords.classifier import classify_chroma
from app.chords.models import ChordEvent
from app.chords.smoothing import smooth_predictions


class ChordDetector:
    def detect(self, features: FeatureSet, beat_map: BeatMap) -> list[ChordEvent]:
        segments = build_beat_segments(features, beat_map)

        labels: list[str] = []
        confidences: list[float] = []
        timestamps: list[float] = []

        for segment in segments:
            label, confidence = classify_chroma(segment["chroma"])
            labels.append(label)
            confidences.append(confidence)
            timestamps.append(segment["start"])

        if not labels:
            return []

        return smooth_predictions(
            labels,
            confidences,
            timestamps,
            features.duration,
            beat_map,
            window_size=1,
            minimum_duration=0.8,
        )


def build_beat_segments(features: FeatureSet, beat_map: BeatMap) -> list[dict]:
    boundaries = build_boundaries(features.duration, beat_map)

    segments: list[dict] = []

    for start, end in zip(boundaries, boundaries[1:]):
        chroma_frames = [
            chroma
            for chroma, timestamp in zip(features.chroma, features.timestamps)
            if start <= timestamp < end
        ]

        if not chroma_frames:
            continue

        segments.append(
            {
                "start": start,
                "end": end,
                "chroma": median_vector(chroma_frames),
            }
        )

    return segments


def build_boundaries(duration: float, beat_map: BeatMap) -> list[float]:
    if len(beat_map.beats) >= 2:
        boundaries = [0.0]
        boundaries.extend(beat for beat in beat_map.beats if 0.0 < beat < duration)
        boundaries.append(duration)
        return sorted(set(boundaries))

    return build_fixed_time_boundaries(duration, seconds=1.0)


def build_fixed_time_boundaries(duration: float, seconds: float) -> list[float]:
    boundaries = [0.0]
    current = seconds

    while current < duration:
        boundaries.append(current)
        current += seconds

    boundaries.append(duration)
    return boundaries


def median_vector(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return [0.0] * 12

    columns = zip(*vectors)
    return [median(list(column)) for column in columns]


def median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2

    if len(ordered) % 2 == 1:
        return ordered[middle]

    return (ordered[middle - 1] + ordered[middle]) / 2