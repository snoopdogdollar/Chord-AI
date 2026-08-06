"""Evaluation module for chord detection accuracy.

Compares predicted ChordEvent lists against ground truth annotations
using mir_eval — the standard MIR evaluation library used by MIREX.

This module does NOT modify any detection logic.  It is read-only
measurement infrastructure.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from app.chords.evaluation_models import (
    Annotation,
    EvaluationResult,
    PerChordMetric,
)
from app.chords.models import ChordEvent


# ---------------------------------------------------------------------------
# Ground truth I/O
# ---------------------------------------------------------------------------

def load_annotations(path: Path) -> list[Annotation]:
    """Load ground truth annotations from a JSON file.

    Expected format:
        {
            "title": "Song Name",
            "annotations": [
                {"start": 0.0, "end": 2.0, "chord": "C"},
                ...
            ]
        }
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        Annotation(start=float(entry["start"]), end=float(entry["end"]), chord=str(entry["chord"]))
        for entry in data["annotations"]
    ]


# ---------------------------------------------------------------------------
# Conversion helpers — our format → mir_eval format
# ---------------------------------------------------------------------------

def _to_mir_eval_label(label: str) -> str:
    """Convert our chord label format to mir_eval format.

    Our format:  C, Am, C7, Am7, N
    mir_eval:    C:maj, A:min, C:7, A:min7, N
    """
    if not label or label == "N":
        return "N"

    # Minor seventh: Am7 → A:min7
    if label.endswith("m7"):
        root = label[:-2]
        return f"{root}:min7"

    # Dominant seventh: C7 → C:7
    if label.endswith("7"):
        root = label[:-1]
        return f"{root}:7"

    # Minor: Am → A:min
    if label.endswith("m"):
        root = label[:-1]
        return f"{root}:min"

    # Major: C → C:maj
    return f"{label}:maj"


def _events_to_mir_eval(events: list[ChordEvent]) -> tuple[np.ndarray, list[str]]:
    """Convert ChordEvent list to mir_eval interval/label arrays."""
    if not events:
        return np.zeros((0, 2)), []

    intervals = np.array([[e.start, e.end] for e in events])
    labels = [_to_mir_eval_label(e.chord) for e in events]
    return intervals, labels


def _annotations_to_mir_eval(annotations: list[Annotation]) -> tuple[np.ndarray, list[str]]:
    """Convert Annotation list to mir_eval interval/label arrays."""
    if not annotations:
        return np.zeros((0, 2)), []

    intervals = np.array([[a.start, a.end] for a in annotations])
    labels = [_to_mir_eval_label(a.chord) for a in annotations]
    return intervals, labels


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate(
    predicted: list[ChordEvent],
    annotations: list[Annotation],
    duration: float,
) -> EvaluationResult:
    """Compare predicted chords against ground truth annotations.

    Uses mir_eval.chord for standard CSR metrics (majmin, root, thirds).
    Also computes a frame-based confusion matrix at 10 ms resolution.

    Parameters
    ----------
    predicted : list[ChordEvent]
        Chord events produced by the detector.
    annotations : list[Annotation]
        Ground truth chord annotations.
    duration : float
        Total audio duration in seconds.

    Returns
    -------
    EvaluationResult
        Evaluation metrics including CSR scores, confusion matrix,
        per-chord precision/recall, and N-rate.
    """
    try:
        import mir_eval
    except ImportError as exc:
        raise ImportError(
            "mir_eval is required for evaluation.  Install it with: "
            "pip install mir_eval"
        ) from exc

    est_intervals, est_labels = _events_to_mir_eval(predicted)
    ref_intervals, ref_labels = _annotations_to_mir_eval(annotations)

    # Handle edge cases.
    if len(ref_intervals) == 0 or len(est_intervals) == 0:
        return EvaluationResult(
            csr_majmin=0.0,
            csr_root=0.0,
            csr_thirds=0.0,
            n_rate=1.0 if len(est_intervals) == 0 else _compute_n_rate(predicted, duration),
            total_duration=duration,
        )

    # mir_eval CSR metrics via the high-level evaluate() function.
    scores = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
    csr_root = scores.get("root", 0.0)
    csr_thirds = scores.get("thirds", 0.0)
    csr_majmin = scores.get("majmin", 0.0)

    # Frame-based confusion matrix and per-chord metrics.
    confusion, correct_duration = _compute_confusion_matrix(predicted, annotations, duration)
    per_chord = _compute_per_chord_metrics(confusion)
    n_rate = _compute_n_rate(predicted, duration)

    return EvaluationResult(
        csr_majmin=csr_majmin,
        csr_root=csr_root,
        csr_thirds=csr_thirds,
        n_rate=n_rate,
        confusion=confusion,
        per_chord=per_chord,
        total_duration=duration,
        total_correct_duration_majmin=correct_duration,
    )


# ---------------------------------------------------------------------------
# Confusion matrix (frame-based, 10 ms resolution)
# ---------------------------------------------------------------------------

def _normalize_chord_label(label: str) -> str:
    """Normalize chord label to root + quality for comparison.

    Maps to simplified major/minor/N vocabulary:
        C, Cm, C7→C, Cm7→Cm, N→N, etc.
    """
    if not label or label == "N":
        return "N"

    # Strip common suffixes for major/minor comparison.
    if label.endswith("m7"):
        return label[:-1]  # Cm7 → Cm (but keep the 'm')... wait
    if label.endswith("7"):
        return label[:-1]  # C7 → C

    return label


def _compute_confusion_matrix(
    predicted: list[ChordEvent],
    annotations: list[Annotation],
    duration: float,
    step: float = 0.01,
) -> tuple[dict[tuple[str, str], float], float]:
    """Compute time-weighted confusion matrix at given resolution.

    Returns (confusion_dict, total_correct_seconds).
    confusion_dict keys are (predicted_label, ground_truth_label).
    """
    confusion: dict[tuple[str, str], float] = defaultdict(float)
    correct_duration = 0.0

    num_frames = int(duration / step)
    for frame_index in range(num_frames):
        time = frame_index * step

        pred_label = _label_at_time(predicted, time)
        ref_label = _label_at_time_annotation(annotations, time)

        pred_norm = _normalize_chord_label(pred_label)
        ref_norm = _normalize_chord_label(ref_label)

        confusion[(pred_norm, ref_norm)] += step

        if pred_norm == ref_norm:
            correct_duration += step

    return dict(confusion), correct_duration


def _label_at_time(events: list[ChordEvent], time: float) -> str:
    """Find chord label at a specific time point."""
    for event in events:
        if event.start <= time < event.end:
            return event.chord
    return "N"


def _label_at_time_annotation(annotations: list[Annotation], time: float) -> str:
    """Find ground truth chord label at a specific time point."""
    for annotation in annotations:
        if annotation.start <= time < annotation.end:
            return annotation.chord
    return "N"


# ---------------------------------------------------------------------------
# Per-chord precision / recall
# ---------------------------------------------------------------------------

def _compute_per_chord_metrics(
    confusion: dict[tuple[str, str], float],
) -> list[PerChordMetric]:
    """Derive per-chord precision and recall from the confusion matrix."""
    all_chords: set[str] = set()
    for pred, ref in confusion:
        all_chords.add(pred)
        all_chords.add(ref)

    metrics: list[PerChordMetric] = []
    for chord in sorted(all_chords):
        if chord == "N":
            continue

        # Total time we predicted this chord.
        total_predicted = sum(
            dur for (pred, _), dur in confusion.items() if pred == chord
        )
        # Total time this chord appears in ground truth.
        total_ground_truth = sum(
            dur for (_, ref), dur in confusion.items() if ref == chord
        )
        # Time we predicted this chord AND it was correct.
        true_positive = confusion.get((chord, chord), 0.0)

        precision = true_positive / total_predicted if total_predicted > 0 else 0.0
        recall = true_positive / total_ground_truth if total_ground_truth > 0 else 0.0

        metrics.append(PerChordMetric(
            chord=chord,
            precision=round(precision, 4),
            recall=round(recall, 4),
            total_predicted_seconds=round(total_predicted, 2),
            total_ground_truth_seconds=round(total_ground_truth, 2),
        ))

    return metrics


# ---------------------------------------------------------------------------
# N-rate
# ---------------------------------------------------------------------------

def _compute_n_rate(predicted: list[ChordEvent], duration: float) -> float:
    """Compute fraction of total duration with no chord prediction."""
    if duration <= 0:
        return 1.0

    covered = sum(max(0.0, event.end - event.start) for event in predicted)
    uncovered = max(0.0, duration - covered)
    return uncovered / duration


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_evaluation_report(result: EvaluationResult, title: str = "") -> str:
    """Format an EvaluationResult as a human-readable text report."""
    lines: list[str] = []

    if title:
        lines.append(f"=== Evaluation: {title} ===")
    lines.append("")

    lines.append("CSR Scores (Chord Symbol Recall)")
    lines.append(f"  majmin : {result.csr_majmin:.4f}  ({result.csr_majmin * 100:.1f}%)")
    lines.append(f"  root   : {result.csr_root:.4f}  ({result.csr_root * 100:.1f}%)")
    lines.append(f"  thirds : {result.csr_thirds:.4f}  ({result.csr_thirds * 100:.1f}%)")
    lines.append("")

    lines.append(f"N-rate   : {result.n_rate:.4f}  ({result.n_rate * 100:.1f}% uncovered)")
    lines.append(f"Duration : {result.total_duration:.1f}s")
    lines.append("")

    if result.per_chord:
        lines.append("Per-Chord Metrics")
        lines.append(f"  {'Chord':<8} {'Precision':>10} {'Recall':>10} {'Pred(s)':>10} {'GT(s)':>10}")
        lines.append(f"  {'-' * 48}")
        for metric in result.per_chord:
            lines.append(
                f"  {metric.chord:<8} {metric.precision:>10.4f} {metric.recall:>10.4f} "
                f"{metric.total_predicted_seconds:>10.2f} {metric.total_ground_truth_seconds:>10.2f}"
            )
        lines.append("")

    if result.confusion:
        lines.append("Confusion Matrix (top entries by duration)")
        sorted_confusion = sorted(result.confusion.items(), key=lambda item: item[1], reverse=True)
        lines.append(f"  {'Predicted':<10} {'Actual':<10} {'Duration(s)':>12}")
        lines.append(f"  {'-' * 32}")
        for (pred, actual), dur in sorted_confusion[:20]:
            match_flag = " [OK]" if pred == actual else ""
            lines.append(f"  {pred:<10} {actual:<10} {dur:>12.2f}s{match_flag}")
        lines.append("")

    return "\n".join(lines)
