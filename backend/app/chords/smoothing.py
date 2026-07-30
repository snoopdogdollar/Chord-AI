from collections import Counter

from app.audio.models import BeatMap
from app.chords.models import ChordEvent


def _snap_to_nearest(value: float, candidates: list[float], tolerance: float) -> float:
    if not candidates:
        return value
    nearest = min(candidates, key=lambda item: abs(item - value))
    return nearest if abs(nearest - value) <= tolerance else value


def smooth_predictions(
    labels: list[str],
    confidences: list[float],
    timestamps: list[float],
    duration: float,
    beat_map: BeatMap,
    *,
    window_size: int = 5,
    minimum_duration: float = 0.6,
) -> list[ChordEvent]:
    if not labels or not timestamps:
        return []

    half_window = max(0, window_size // 2)
    smoothed: list[str] = []
    for index in range(len(labels)):
        start = max(0, index - half_window)
        end = min(len(labels), index + half_window + 1)
        label = Counter(labels[start:end]).most_common(1)[0][0]
        smoothed.append(label)

    events: list[ChordEvent] = []
    segment_label = smoothed[0]
    segment_start_index = 0
    for index, label in enumerate(smoothed[1:], start=1):
        if label != segment_label:
            _append_event(events, segment_label, segment_start_index, index, timestamps, confidences, duration)
            segment_label = label
            segment_start_index = index
    _append_event(events, segment_label, segment_start_index, len(smoothed), timestamps, confidences, duration)

    merged = _merge_short_events(events, minimum_duration)
    return _snap_events_to_beats(merged, beat_map)


def _append_event(
    events: list[ChordEvent],
    label: str,
    start_index: int,
    end_index: int,
    timestamps: list[float],
    confidences: list[float],
    duration: float,
) -> None:
    if label == "N":
        return
    start = timestamps[start_index]
    end = timestamps[end_index] if end_index < len(timestamps) else duration
    if end <= start:
        return
    confidence_values = confidences[start_index:end_index] or [0.0]
    events.append(ChordEvent(start=start, end=end, chord=label, confidence=sum(confidence_values) / len(confidence_values)))


def _merge_short_events(events: list[ChordEvent], minimum_duration: float) -> list[ChordEvent]:
    merged: list[ChordEvent] = []
    for event in events:
        if merged and event.chord == merged[-1].chord:
            previous = merged.pop()
            merged.append(
                ChordEvent(
                    start=previous.start,
                    end=event.end,
                    chord=event.chord,
                    confidence=(previous.confidence + event.confidence) / 2,
                )
            )
            continue
        if event.end - event.start < minimum_duration and merged:
            previous = merged.pop()
            merged.append(
                ChordEvent(
                    start=previous.start,
                    end=event.end,
                    chord=previous.chord,
                    confidence=min(previous.confidence, event.confidence),
                )
            )
            continue
        merged.append(event)
    return merged


def _snap_events_to_beats(events: list[ChordEvent], beat_map: BeatMap) -> list[ChordEvent]:
    if not beat_map.beats:
        return events

    snapped: list[ChordEvent] = []
    for index, event in enumerate(events):
        start = 0.0 if index == 0 else _snap_to_nearest(event.start, beat_map.beats, 0.18)
        end = event.end
        if index < len(events) - 1:
            end = _snap_to_nearest(event.end, beat_map.beats, 0.18)
        if end > start:
            snapped.append(ChordEvent(start=start, end=end, chord=event.chord, confidence=event.confidence))
    return snapped
