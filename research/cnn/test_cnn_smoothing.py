"""Synthetic temporal regressions; these do not establish real-audio accuracy."""
import unittest
import numpy as np
from cnn_smoothing import smooth_probabilities, decode_segments


class SmoothingTests(unittest.TestCase):
    def test_weak_one_frame_flip_is_removed_without_changing_input(self):
        times = np.arange(9) * 0.1161
        probabilities = np.tile([0.1, 0.9], (9, 1))
        probabilities[4] = [0.55, 0.45]
        original = probabilities.copy()
        result = smooth_probabilities(times, probabilities, 0.4)
        self.assertTrue(np.all(result.argmax(1) == 1))
        np.testing.assert_array_equal(probabilities, original)
        np.testing.assert_allclose(result.sum(1), 1)

    def test_symmetric_clear_transition_keeps_boundary(self):
        times = np.arange(10) * 0.1
        probabilities = np.array([[0.95, 0.05]] * 5 + [[0.05, 0.95]] * 5)
        raw = decode_segments(times, probabilities, 1.0, ['Am', 'F'])
        result = decode_segments(times, smooth_probabilities(times, probabilities, 0.4), 1.0, ['Am', 'F'])
        self.assertEqual(raw, result)
        self.assertAlmostEqual(result[0]['end'], 0.45)

    def test_zero_tiny_windows_and_single_frame_are_identity(self):
        times = [0, 0.12, 0.24]
        probabilities = np.array([[0.1, 0.9], [0.8, 0.2], [0.3, 0.7]])
        for seconds in [0, 0.01]:
            np.testing.assert_allclose(smooth_probabilities(times, probabilities, seconds), probabilities)
        np.testing.assert_allclose(smooth_probabilities([0], [[0.1, 0.9]], 0.4), [[0.1, 0.9]])

    def test_edges_average_only_available_frames(self):
        result = smooth_probabilities([0, 0.1, 0.2], [[1, 0], [0, 1], [0, 1]], 0.3)
        np.testing.assert_allclose(result[0], [0.5, 0.5])
        np.testing.assert_allclose(result[-1], [0, 1])

    def test_decoder_covers_audio_without_gaps(self):
        result = decode_segments([0, 0.12, 0.24], [[1, 0], [0, 1], [1, 0]], 0.3, ['C', 'Am'])
        self.assertEqual(result[0]['start'], 0)
        self.assertEqual(result[-1]['end'], 0.3)
        for left, right in zip(result, result[1:]):
            self.assertEqual(left['end'], right['start'])

    def test_invalid_data_fails_explicitly(self):
        for seconds in [-1, float('nan')]:
            with self.assertRaises(ValueError):
                smooth_probabilities([0], [[1, 0]], seconds)
        for times, probs in [([], []), ([0, 0], [[1, 0], [1, 0]]), ([0], [[0.2, 0.3]]), ([0], [[float('nan'), 1]])]:
            with self.assertRaises(ValueError):
                smooth_probabilities(times, probs)


if __name__ == '__main__':
    unittest.main()
