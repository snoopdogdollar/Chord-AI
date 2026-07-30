import math

from app.chords.templates import CHORD_TEMPLATES


SEVENTH_CHORDS = {"7", "m7"}


def normalize_chroma(chroma_vector: list[float]) -> list[float]:
    peak = max(chroma_vector, default=0.0)
    if peak <= 0.001:
        return [0.0] * 12

    normalized = [max(0.0, value / peak) for value in chroma_vector]

    # Giảm noise nhỏ.
    return [value if value >= 0.08 else 0.0 for value in normalized]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return numerator / (left_norm * right_norm)


def non_chord_penalty(chroma_vector: list[float], template: list[float]) -> float:
    outside_values = [
        chroma
        for chroma, template_value in zip(chroma_vector, template)
        if template_value == 0.0
    ]

    if not outside_values:
        return 0.0

    return sum(outside_values) / len(outside_values) * 0.18


def has_seventh_evidence(label: str, chroma_vector: list[float]) -> bool:
    if label.endswith("m7"):
        root = label[:-2]
    elif label.endswith("7"):
        root = label[:-1]
    else:
        return True

    pitch_classes = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    root_index = pitch_classes.index(root)
    seventh_index = (root_index + 10) % 12

    return chroma_vector[seventh_index] >= 0.18


def classify_chroma(chroma_vector: list[float]) -> tuple[str, float]:
    if len(chroma_vector) != 12:
        return "N", 0.0

    chroma = normalize_chroma(chroma_vector)

    if max(chroma, default=0.0) <= 0.001:
        return "N", 0.0

    scored: list[tuple[str, float]] = []

    for label, template in CHORD_TEMPLATES.items():
        score = cosine_similarity(chroma, template)
        score -= non_chord_penalty(chroma, template)

        if not has_seventh_evidence(label, chroma):
            score -= 0.12

        scored.append((label, score))

    scored.sort(key=lambda item: item[1], reverse=True)

    best_label, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0
    margin = best_score - second_score

    if best_score < 0.35 or margin < 0.03:
        return "N", max(0.0, min(1.0, best_score))

    confidence = (best_score * 0.75) + (margin * 1.5)
    confidence = max(0.0, min(1.0, confidence))

    return best_label, confidence