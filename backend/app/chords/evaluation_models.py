from dataclasses import dataclass, field


@dataclass(frozen=True)
class Annotation:
    """A single ground truth chord annotation with start/end time."""

    start: float
    end: float
    chord: str


@dataclass(frozen=True)
class PerChordMetric:
    """Precision and recall for a single chord label."""

    chord: str
    precision: float
    recall: float
    total_predicted_seconds: float
    total_ground_truth_seconds: float


@dataclass(frozen=True)
class EvaluationResult:
    """Complete evaluation result comparing predictions against ground truth."""

    # Chord Symbol Recall scores from mir_eval.
    csr_majmin: float
    csr_root: float
    csr_thirds: float

    # Fraction of total duration classified as "N" (no chord).
    n_rate: float

    # Confusion counts: {(predicted, actual): duration_seconds}.
    confusion: dict[tuple[str, str], float] = field(default_factory=dict)

    # Per-chord precision/recall.
    per_chord: list[PerChordMetric] = field(default_factory=list)

    # Raw numbers.
    total_duration: float = 0.0
    total_correct_duration_majmin: float = 0.0
