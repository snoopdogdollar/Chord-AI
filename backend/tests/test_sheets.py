import unittest

from app.chords.models import ChordEvent
from app.sheets.generator import generate_sheet_text


class SheetGeneratorTests(unittest.TestCase):
    def test_generates_song_section_without_inferred_parts(self):
        content = generate_sheet_text(
            "Test Song",
            [
                ChordEvent(0, 2, "C", 0.9),
                ChordEvent(2, 4, "G", 0.8),
                ChordEvent(4, 6, "Am", 0.85),
                ChordEvent(6, 8, "F", 0.82),
            ],
        )

        self.assertIn("[Song]", content)
        self.assertIn("Timeline", content)
        self.assertNotIn("[Verse]", content)


if __name__ == "__main__":
    unittest.main()
