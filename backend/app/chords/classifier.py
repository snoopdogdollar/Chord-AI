import math

from app.chords.templates import CHORD_TEMPLATES




def normalize_chroma(chroma_vector: list[float]) -> list[float]:
    peak = max(chroma_vector, default=0.0)
    if peak <= 0.001:
        return [0.0] * 12

    return [max(0.0, value / peak) for value in chroma_vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return numerator / (left_norm * right_norm)


def classify_chroma(
    chroma_vector: list[float],
    diatonic_chords: set[str] | None = None,
) -> tuple[str, float]:
    if len(chroma_vector) != 12:
        return "N", 0.0

    chroma = normalize_chroma(chroma_vector)

    if max(chroma, default=0.0) <= 0.001:
        return "N", 0.0

    scored: list[tuple[str, float]] = []

    for label, template in CHORD_TEMPLATES.items():
        score = cosine_similarity(chroma, template)
        if diatonic_chords and label in diatonic_chords:
            score += 0.06
        scored.append((label, score))

    scored.sort(key=lambda item: item[1], reverse=True)

    best_label, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0
    margin = best_score - second_score

    if best_score < 0.15:
        return "N", max(0.0, min(1.0, best_score))

    confidence = (best_score * 0.75) + (margin * 1.5)
    confidence = max(0.0, min(1.0, confidence))

    return best_label, confidence