import unittest

from app.audio.models import BeatMap, FeatureSet
from app.chords.detector import ChordDetector
from app.chords.classifier import classify_chroma
from app.chords.smoothing import smooth_predictions
from app.chords.templates import CHORD_TEMPLATES


class ChordClassifierTests(unittest.TestCase):
    def test_classifies_major_template(self):
        label, confidence = classify_chroma(CHORD_TEMPLATES["C"])

        self.assertEqual(label, "C")
        self.assertGreaterEqual(confidence, 0.90)

    def test_classifies_minor_template(self):
        label, confidence = classify_chroma(CHORD_TEMPLATES["Am"])

        self.assertEqual(label, "Am")
        self.assertGreaterEqual(confidence, 0.90)

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

class ChordDetectorIntegrationTests(unittest.TestCase):
    def test_detects_c_g_am_f_from_beat_grouped_chroma(self):
        # 4 chords × 4 beats per bar = 16 beats total
        # Each bar gets 4 chroma frames matching the chord template
        features = FeatureSet(
            chroma=[
                CHORD_TEMPLATES["C"], CHORD_TEMPLATES["C"],
                CHORD_TEMPLATES["C"], CHORD_TEMPLATES["C"],
                CHORD_TEMPLATES["G"], CHORD_TEMPLATES["G"],
                CHORD_TEMPLATES["G"], CHORD_TEMPLATES["G"],
                CHORD_TEMPLATES["Am"], CHORD_TEMPLATES["Am"],
                CHORD_TEMPLATES["Am"], CHORD_TEMPLATES["Am"],
                CHORD_TEMPLATES["F"], CHORD_TEMPLATES["F"],
                CHORD_TEMPLATES["F"], CHORD_TEMPLATES["F"],
            ],
            timestamps=[
                0.0, 0.5, 1.0, 1.5,
                2.0, 2.5, 3.0, 3.5,
                4.0, 4.5, 5.0, 5.5,
                6.0, 6.5, 7.0, 7.5,
            ],
            sample_rate=44100,
            hop_length=2048,
            duration=8.0,
        )
        beat_map = BeatMap(
            bpm=120,
            beats=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5,
                   4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5],
        )

        events = ChordDetector().detect(features, beat_map)

        self.assertEqual([event.chord for event in events], ["C", "G", "Am", "F"])

if __name__ == "__main__":
    unittest.main()

