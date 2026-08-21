import math

PITCH_CLASSES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

QUALITY_WEIGHTS = {
    "": {0: 1.0, 4: 0.85, 7: 0.50},
    "m": {0: 1.0, 3: 0.85, 7: 0.50},
}


def build_templates() -> dict[str, list[float]]:
    templates: dict[str, list[float]] = {}
    for root_index, root in enumerate(PITCH_CLASSES):
        for suffix, intervals in QUALITY_WEIGHTS.items():
            vector = [0.0] * 12
            for interval, weight in intervals.items():
                vector[(root_index + interval) % 12] = weight
            # L2-normalize so cosine similarity measures angle, not magnitude
            norm = math.sqrt(sum(v * v for v in vector))
            if norm > 0:
                vector = [v / norm for v in vector]
            templates[f"{root}{suffix}"] = vector
    return templates


CHORD_TEMPLATES = build_templates()

