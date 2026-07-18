import unittest

from app.audio.models import BeatMap
from app.chords.classifier import classify_chroma
from app.chords.smoothing import smooth_predictions
from app.chords.templates import CHORD_TEMPLATES


class ChordClassifierTests(unittest.TestCase):
    def test_classifies_major_template(self):
        label, confidence = classify_chroma(CHORD_TEMPLATES["C"])

        self.assertEqual(label, "C")
        self.assertGreaterEqual(confidence, 0.99)

    def test_classifies_minor_template(self):
        label, confidence = classify_chroma(CHORD_TEMPLATES["Am"])

        self.assertEqual(label, "Am")
        self.assertGreaterEqual(confidence, 0.99)

    def test_silence_returns_no_chord(self):
        label, confidence = classify_chroma([0.0] * 12)

        self.assertEqual(label, "N")
        self.assertEqual(confidence, 0.0)


class SmoothingTests(unittest.TestCase):
    def test_merges_duplicate_predictions(self):
        events = smooth_predictions(
            labels=["C", "C", "C", "G", "G", "G"],
            confidences=[0.9, 0.8, 0.9, 0.7, 0.8, 0.9],
            timestamps=[0, 1, 2, 3, 4, 5],
            duration=6,
            beat_map=BeatMap(bpm=120, beats=[0, 1, 2, 3, 4, 5, 6]),
            window_size=1,
        )

        self.assertEqual([event.chord for event in events], ["C", "G"])
        self.assertEqual(events[0].start, 0.0)
        self.assertEqual(events[-1].end, 6)


if __name__ == "__main__":
    unittest.main()
