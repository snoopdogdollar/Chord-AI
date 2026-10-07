"""Build a display score from timed chords. Meter/downbeats are assumptions, not detections."""

from bisect import bisect_right
import json
import math
from statistics import median

from app.chords.models import ChordEvent
from app.sheets.generator import generate_sheet_text


def build_score(title: str, chords: list[ChordEvent], *, duration: float | None = None,
                bpm: float | None = None, beats: list[float] | None = None) -> dict:
    events = sorted((c for c in chords if math.isfinite(c.start) and math.isfinite(c.end)
                     and c.end > c.start and c.end > 0), key=lambda c: c.start)
    end = max(duration or 0, max((c.end for c in events), default=0))
    detected = sorted(set(b for b in (beats or []) if math.isfinite(b) and 0 <= b < end))
    tempo = bpm if bpm and math.isfinite(bpm) and bpm > 0 else None
    if len(detected) >= 2:
        step = median(b - a for a, b in zip(detected, detected[1:]))
        grid = list(detected)
        # Extend the detected beat grid to cover leading/trailing audio.
        while grid[0] > 1e-6:
            grid.insert(0, max(0, grid[0] - step))
        source = "detected_beats"
    else:
        step = 60 / tempo if tempo else 0.5
        grid = [0.0]
        source = "estimated_tempo" if tempo else "default_tempo"
    while grid[-1] < end or (len(grid) - 1) % 4:
        grid.append(grid[-1] + step)

    def beat_position(time: float) -> float:
        i = min(max(0, bisect_right(grid, time) - 1), len(grid) - 2)
        return i + (time - grid[i]) / (grid[i + 1] - grid[i])

    # Include explicit gaps, so a previous chord never falsely continues through silence/unknown audio.
    changes = [(0.0, "N.C.")]
    for event in events:
        changes.append((max(0, event.start), "N.C." if event.chord == "N" else event.chord))
        changes.append((event.end, "N.C."))
    changes.sort(key=lambda item: item[0])
    merged: list[tuple[float, str]] = []
    for time, name in changes:
        if merged and merged[-1][0] == time:
            merged[-1] = (time, name)
        else:
            merged.append((time, name))
    transitions = []
    for item in merged:
        if not transitions or item[1] != transitions[-1][1]:
            transitions.append(item)
    times = [item[0] for item in transitions]
    measures = []
    if events:
        for index in range(0, len(grid) - 1, 4):
            start, stop = grid[index], min(end, grid[index + 4])
            if start >= end:
                break
            active = transitions[max(0, bisect_right(times, start) - 1)][1]
            labels = [{"beat": 0.0, "chord": active}]
            for time, name in transitions[bisect_right(times, start):bisect_right(times, stop)]:
                if time < stop:
                    labels.append({"beat": round(beat_position(time) - index, 5), "chord": name})
            measures.append({"number": len(measures) + 1, "start": start, "end": stop,
                             "beats": min(4.0, beat_position(stop) - index), "chords": labels})
    return {"version": 2, "title": title.strip() or "Untitled Song", "meter": "4/4",
            "bpm": tempo, "grid_source": source, "measures": measures,
            "text": generate_sheet_text(title, events),
            "notice": "Estimated 4/4 bars; meter and downbeats have not been detected.",
            "timing_note": {"detected_beats": "Spacing follows detected beats.",
                            "estimated_tempo": "Spacing uses the saved tempo; beat positions are unavailable.",
                            "default_tempo": "No beat data available; spacing uses a 120 BPM guide."}[source]}


def encode_score(score: dict) -> str:
    return json.dumps(score, ensure_ascii=False, allow_nan=False)


def decode_score(content: str) -> dict | None:
    try:
        score = json.loads(content)
    except (ValueError, TypeError):
        return None
    return score if isinstance(score, dict) and score.get("version") == 2 else None
