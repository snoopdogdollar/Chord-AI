import unittest
from xml.etree import ElementTree

from app.chords.models import ChordEvent
from app.sheets.score import build_score, decode_score, encode_score
from app.sheets.notation import preview_pages, score_pages


class ScoreTests(unittest.TestCase):
    def test_changes_use_detected_beat_positions_and_carry_across_bars(self):
        score = build_score("Song", [ChordEvent(0, 1.75, "C", .9), ChordEvent(1.75, 5, "G", .9)],
                            beats=[0, .5, 1.2, 2.3, 3, 3.5, 4, 4.5], bpm=120, duration=5)
        self.assertEqual(score["grid_source"], "detected_beats")
        self.assertEqual(score["measures"][0]["end"], 3)
        self.assertEqual(score["measures"][0]["chords"],
                         [{"beat": 0, "chord": "C"}, {"beat": 2.5, "chord": "G"}])
        self.assertEqual(score["measures"][1]["chords"], [{"beat": 0, "chord": "G"}])

    def test_exact_boundary_change_belongs_to_next_bar(self):
        score = build_score("Song", [ChordEvent(0, 2, "C", .9), ChordEvent(2, 4, "Am", .9)], bpm=120)
        self.assertEqual(len(score["measures"]), 2)
        self.assertEqual(score["measures"][0]["chords"], [{"beat": 0, "chord": "C"}])
        self.assertEqual(score["measures"][1]["chords"], [{"beat": 0, "chord": "Am"}])

    def test_unknown_gaps_and_partial_last_bar(self):
        score = build_score("Song", [ChordEvent(.5, 1, "C", .9), ChordEvent(2, 2.25, "N", .1)], bpm=120)
        self.assertEqual(score["measures"][0]["chords"],
                         [{"beat": 0, "chord": "N.C."}, {"beat": 1, "chord": "C"},
                          {"beat": 2, "chord": "N.C."}])
        self.assertEqual(score["measures"][-1]["beats"], .5)

    def test_missing_and_invalid_beats_have_explicit_fallback(self):
        score = build_score("Song", [ChordEvent(0, 2, "C", .9)], beats=[float("nan"), -1])
        self.assertEqual(score["grid_source"], "default_tempo")
        self.assertIn("120 BPM", score["timing_note"])
        self.assertIsNone(score["bpm"])
        self.assertEqual(len(score["measures"]), 1)

    def test_empty_score_and_legacy_content(self):
        score = build_score("Song", [])
        self.assertEqual(score["measures"], [])
        self.assertIn("No stable chords", preview_pages(score)[0])
        self.assertIsNone(decode_score("old text sheet"))
        self.assertEqual(decode_score(encode_score(score)), score)

    def test_svg_escapes_title_and_pdf_font_supports_vietnamese(self):
        title = 'Mưa <script>alert("x")</script> & Đường về'
        score = build_score(title, [ChordEvent(0, 2, "F#7", .9)], bpm=120)
        svg = preview_pages(score)[0]
        root = ElementTree.fromstring(svg)
        self.assertEqual(root.findall(".//{http://www.w3.org/2000/svg}script"), [])
        self.assertIn(title, "".join(root.itertext()))
        from reportlab.pdfbase import pdfmetrics
        from app.sheets.notation import FONT
        for char in "Mưa Đường về ngắm":
            self.assertIn(ord(char), pdfmetrics.getFont(FONT).face.charToGlyph)

    def test_long_score_paginates_and_keeps_last_chord(self):
        chords = [ChordEvent(i * 2, (i + 1) * 2, "C" if i < 89 else "F#7", .9) for i in range(90)]
        score = build_score("A long song", chords, bpm=120)
        pages = preview_pages(score)
        self.assertGreater(len(pages), 1)
        self.assertIn("F#7", pages[-1])
        self.assertIn(f"{len(pages)} / {len(pages)}", pages[-1])

    def test_dense_changes_are_not_dropped_or_overlapping(self):
        from app.sheets.notation import label_layout, register_font
        register_font()
        chords = [ChordEvent(i / 10, (i + 1) / 10, "Cmaj7" if i % 2 else "F#7", .9) for i in range(20)]
        score = build_score("Dense", chords, bpm=120)
        placed, lanes = label_layout(score["measures"][0], 100, 450)
        self.assertEqual(len(placed), 20)
        self.assertGreater(lanes, 1)
        self.assertEqual(len(score_pages(score)), 1)


if __name__ == "__main__":
    unittest.main()
