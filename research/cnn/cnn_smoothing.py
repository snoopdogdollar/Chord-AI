"""Offline temporal smoothing and decoding, independent of the CNN model."""
import numpy as np


def validate_frames(times, probabilities):
    times = np.asarray(times, dtype=np.float64)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if (times.ndim != 1 or not len(times) or probabilities.ndim != 2
            or probabilities.shape[0] != len(times) or probabilities.shape[1] == 0):
        raise ValueError('Expected nonempty times [T] and probabilities [T, classes]')
    if (not np.isfinite(times).all() or times[0] < 0 or np.any(np.diff(times) <= 0)
            or not np.isfinite(probabilities).all() or np.any(probabilities < 0)
            or not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-5, rtol=0)):
        raise ValueError('Invalid times or probability distribution')
    return times, probabilities


def smooth_probabilities(times, probabilities, window_seconds=0.4):
    """Centered mean within +/- half the window; available frames only at edges.

    Zero disables smoothing. No class-specific rules, minimum segment length,
    or retraining. This offline operation uses future as well as past frames.
    """
    times, probabilities = validate_frames(times, probabilities)
    if not np.isfinite(window_seconds) or window_seconds < 0:
        raise ValueError('window_seconds must be finite and nonnegative')
    if window_seconds == 0:
        return probabilities.copy()
    half = window_seconds / 2
    left = np.searchsorted(times, times - half - 1e-9, side='left')
    right = np.searchsorted(times, times + half + 1e-9, side='right')
    cumulative = np.vstack([np.zeros((1, probabilities.shape[1])), probabilities.cumsum(axis=0)])
    return (cumulative[right] - cumulative[left]) / (right - left)[:, None]


def decode_segments(times, probabilities, duration, labels):
    """Argmax then merge adjacent identical labels, preserving the time grid."""
    times, probabilities = validate_frames(times, probabilities)
    if not np.isfinite(duration) or duration <= times[-1] or len(labels) != probabilities.shape[1]:
        raise ValueError('Duration or label count does not match the frames')
    edges = np.r_[0.0, (times[:-1] + times[1:]) / 2, duration]
    segments = []
    for i, label_id in enumerate(probabilities.argmax(1)):
        label = labels[int(label_id)]
        if segments and segments[-1]['chord'] == label:
            segments[-1]['end'] = float(edges[i+1])
        else:
            segments.append(dict(start=float(edges[i]), end=float(edges[i+1]), chord=label))
    return segments
