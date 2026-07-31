import unittest

from app.core.errors import InvalidAnalysisRangeError
from app.services.songs import validate_analysis_range


class AnalysisRangeValidationTests(unittest.TestCase):
    def test_allows_missing_analysis_range(self):
        self.assertEqual(validate_analysis_range(None, None), (None, None))

    def test_allows_valid_analysis_range(self):
        self.assertEqual(validate_analysis_range(2.5, 10.0), (2.5, 10.0))

    def test_requires_both_range_boundaries(self):
        with self.assertRaises(InvalidAnalysisRangeError):
            validate_analysis_range(2.5, None)

        with self.assertRaises(InvalidAnalysisRangeError):
            validate_analysis_range(None, 10.0)

    def test_rejects_negative_start(self):
        with self.assertRaises(InvalidAnalysisRangeError):
            validate_analysis_range(-0.1, 10.0)

    def test_rejects_end_before_or_equal_to_start(self):
        with self.assertRaises(InvalidAnalysisRangeError):
            validate_analysis_range(10.0, 10.0)

        with self.assertRaises(InvalidAnalysisRangeError):
            validate_analysis_range(10.0, 9.9)

    def test_rejects_range_shorter_than_one_second(self):
        with self.assertRaises(InvalidAnalysisRangeError):
            validate_analysis_range(10.0, 10.5)


if __name__ == "__main__":
    unittest.main()
