import math

from app.chords.templates import CHORD_TEMPLATES


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def classify_chroma(chroma_vector: list[float]) -> tuple[str, float]:
    if len(chroma_vector) != 12 or max(chroma_vector, default=0.0) <= 0.001:
        return "N", 0.0

    best_label = "N"
    best_score = 0.0
    for label, template in CHORD_TEMPLATES.items():
        score = cosine_similarity(chroma_vector, template)
        if score > best_score:
            best_label = label
            best_score = score

    if best_score < 0.35:
        return "N", best_score
    return best_label, max(0.0, min(1.0, best_score))
