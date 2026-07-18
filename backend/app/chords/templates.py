PITCH_CLASSES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

QUALITY_INTERVALS = {
    "": (0, 4, 7),
    "m": (0, 3, 7),
    "7": (0, 4, 7, 10),
    "m7": (0, 3, 7, 10),
}


def build_templates() -> dict[str, list[float]]:
    templates: dict[str, list[float]] = {}
    for root_index, root in enumerate(PITCH_CLASSES):
        for suffix, intervals in QUALITY_INTERVALS.items():
            vector = [0.0] * 12
            for interval in intervals:
                vector[(root_index + interval) % 12] = 1.0
            templates[f"{root}{suffix}"] = vector
    return templates


CHORD_TEMPLATES = build_templates()
