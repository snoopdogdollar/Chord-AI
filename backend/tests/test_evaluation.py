"""Unit tests for the chord evaluation module.

Tests cover:
- CSR computation with mir_eval integration
- Confusion matrix generation
- Per-chord precision/recall
- Edge cases (empty predictions, perfect match, total mismatch)
- N-rate calculation
- Report formatting
"""

import unittest

from app.chords.evaluation import (
    evaluate,
    format_evaluation_report,
    _compute_n_rate,
    _normalize_chord_label,
)
from app.chords.evaluation_models import Annotation, EvaluationResult
from app.chords.models import ChordEvent


class TestNormalizeChordLabel(unittest.TestCase):
    def test_major_chord_unchanged(self):
        self.assertEqual(_normalize_chord_label("C"), "C")
        self.assertEqual(_normalize_chord_label("G"), "G")

    def test_minor_chord_unchanged(self):
        self.assertEqual(_normalize_chord_label("Am"), "Am")
        self.assertEqual(_normalize_chord_label("Dm"), "Dm")

    def test_seventh_maps_to_major(self):
        self.assertEqual(_normalize_chord_label("C7"), "C")
        self.assertEqual(_normalize_chord_label("G7"), "G")

    def test_minor_seventh_maps_to_minor(self):
        self.assertEqual(_normalize_chord_label("Cm7"), "Cm")
        self.assertEqual(_normalize_chord_label("Am7"), "Am")

    def test_no_chord(self):
        self.assertEqual(_normalize_chord_label("N"), "N")
        self.assertEqual(_normalize_chord_label(""), "N")


class TestNRate(unittest.TestCase):
    def test_full_coverage(self):
        events = [ChordEvent(start=0.0, end=10.0, chord="C", confidence=0.9)]
        self.assertAlmostEqual(_compute_n_rate(events, 10.0), 0.0)

    def test_no_coverage(self):
        self.assertAlmostEqual(_compute_n_rate([], 10.0), 1.0)

    def test_partial_coverage(self):
        events = [ChordEvent(start=0.0, end=5.0, chord="C", confidence=0.9)]
        self.assertAlmostEqual(_compute_n_rate(events, 10.0), 0.5)

    def test_zero_duration(self):
        self.assertAlmostEqual(_compute_n_rate([], 0.0), 1.0)


class TestEvaluatePerfectMatch(unittest.TestCase):
    """When predictions exactly match ground truth, CSR should be 1.0."""

    def test_perfect_match(self):
        predicted = [
            ChordEvent(start=0.0, end=2.0, chord="C", confidence=0.9),
            ChordEvent(start=2.0, end=4.0, chord="G", confidence=0.9),
            ChordEvent(start=4.0, end=6.0, chord="Am", confidence=0.9),
            ChordEvent(start=6.0, end=8.0, chord="F", confidence=0.9),
        ]
        annotations = [
            Annotation(start=0.0, end=2.0, chord="C"),
            Annotation(start=2.0, end=4.0, chord="G"),
            Annotation(start=4.0, end=6.0, chord="Am"),
            Annotation(start=6.0, end=8.0, chord="F"),
        ]

        result = evaluate(predicted, annotations, duration=8.0)

        self.assertAlmostEqual(result.csr_majmin, 1.0, places=2)
        self.assertAlmostEqual(result.csr_root, 1.0, places=2)
        self.assertAlmostEqual(result.n_rate, 0.0, places=2)


class TestEvaluateTotalMismatch(unittest.TestCase):
    """When every prediction is wrong, CSR should be 0.0."""

    def test_total_mismatch(self):
        predicted = [
            ChordEvent(start=0.0, end=4.0, chord="D", confidence=0.9),
            ChordEvent(start=4.0, end=8.0, chord="E", confidence=0.9),
        ]
        annotations = [
            Annotation(start=0.0, end=4.0, chord="C"),
            Annotation(start=4.0, end=8.0, chord="G"),
        ]

        result = evaluate(predicted, annotations, duration=8.0)

        self.assertAlmostEqual(result.csr_majmin, 0.0, places=2)
        self.assertAlmostEqual(result.csr_root, 0.0, places=2)


class TestEvaluatePartialMatch(unittest.TestCase):
    """When half the predictions are correct, CSR should be ~0.5."""

    def test_half_correct(self):
        predicted = [
            ChordEvent(start=0.0, end=4.0, chord="C", confidence=0.9),
            ChordEvent(start=4.0, end=8.0, chord="D", confidence=0.9),
        ]
        annotations = [
            Annotation(start=0.0, end=4.0, chord="C"),
            Annotation(start=4.0, end=8.0, chord="G"),
        ]

        result = evaluate(predicted, annotations, duration=8.0)

        self.assertAlmostEqual(result.csr_majmin, 0.5, places=1)


class TestEvaluateEmptyPredictions(unittest.TestCase):
    """Empty predictions should yield CSR = 0.0."""

    def test_empty_predictions(self):
        annotations = [
            Annotation(start=0.0, end=4.0, chord="C"),
        ]

        result = evaluate([], annotations, duration=4.0)

        self.assertEqual(result.csr_majmin, 0.0)
        self.assertAlmostEqual(result.n_rate, 1.0)


class TestEvaluateEmptyAnnotations(unittest.TestCase):
    """Empty ground truth should yield CSR = 0.0."""

    def test_empty_annotations(self):
        predicted = [
            ChordEvent(start=0.0, end=4.0, chord="C", confidence=0.9),
        ]

        result = evaluate(predicted, [], duration=4.0)

        self.assertEqual(result.csr_majmin, 0.0)


class TestConfusionMatrix(unittest.TestCase):
    """Confusion matrix should capture which chords are confused."""

    def test_confusion_entries(self):
        predicted = [
            ChordEvent(start=0.0, end=4.0, chord="Am", confidence=0.9),
        ]
        annotations = [
            Annotation(start=0.0, end=4.0, chord="C"),
        ]

        result = evaluate(predicted, annotations, duration=4.0)

        # Should have (Am, C) as the main confusion entry.
        self.assertIn(("Am", "C"), result.confusion)
        self.assertGreater(result.confusion[("Am", "C")], 3.5)  # ~4 seconds


class TestPerChordMetrics(unittest.TestCase):
    """Per-chord precision and recall."""

    def test_perfect_precision_recall(self):
        predicted = [
            ChordEvent(start=0.0, end=4.0, chord="C", confidence=0.9),
        ]
        annotations = [
            Annotation(start=0.0, end=4.0, chord="C"),
        ]

        result = evaluate(predicted, annotations, duration=4.0)

        c_metrics = [m for m in result.per_chord if m.chord == "C"]
        self.assertEqual(len(c_metrics), 1)
        self.assertAlmostEqual(c_metrics[0].precision, 1.0, places=2)
        self.assertAlmostEqual(c_metrics[0].recall, 1.0, places=2)


class TestFormatReport(unittest.TestCase):
    """Report formatting should not crash and should contain key info."""

    def test_report_contains_csr(self):
        result = EvaluationResult(
            csr_majmin=0.65,
            csr_root=0.72,
            csr_thirds=0.68,
            n_rate=0.05,
            total_duration=120.0,
        )

        report = format_evaluation_report(result, title="Test Song")

        self.assertIn("65.0%", report)
        self.assertIn("72.0%", report)
        self.assertIn("Test Song", report)


if __name__ == "__main__":
    unittest.main()
