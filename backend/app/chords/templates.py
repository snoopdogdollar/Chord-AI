PITCH_CLASSES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

QUALITY_WEIGHTS = {
    "": {0: 1.0, 4: 0.85, 7: 0.75},
    "m": {0: 1.0, 3: 0.85, 7: 0.75},
    "7": {0: 1.0, 4: 0.85, 7: 0.75, 10: 0.55},
    "m7": {0: 1.0, 3: 0.85, 7: 0.75, 10: 0.55},
}


def build_templates() -> dict[str, list[float]]:
    templates: dict[str, list[float]] = {}
    for root_index, root in enumerate(PITCH_CLASSES):
        for suffix, intervals in QUALITY_WEIGHTS.items():
            vector = [0.0] * 12
            for interval in intervals:
                vector[(root_index + interval) % 12] = 1.0
            templates[f"{root}{suffix}"] = vector
    return templates


CHORD_TEMPLATES = build_templates()
