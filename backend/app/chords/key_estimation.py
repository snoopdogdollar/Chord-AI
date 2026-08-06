"""Krumhansl-Schmuckler Key Estimation module for Chord AI.

Estimates the global key/tonic of a song from its global average chroma vector,
and provides diatonic scale triad lookup to guide chord classification priors.
"""

from __future__ import annotations

import numpy as np

PITCHES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Krumhansl-Schmuckler Key Profiles (Krumhansl, 1990)
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def estimate_key(global_chroma_vector: list[float]) -> tuple[str, str]:
    """Estimate key (tonic root, mode) from global average chroma vector.

    Parameters
    ----------
    global_chroma_vector : list[float]
        Average chroma vector across all audio frames (length 12).

    Returns
    -------
    tuple[str, str]
        (root, mode) e.g. ("C", "maj") or ("A", "min").
    """
    if not global_chroma_vector or len(global_chroma_vector) != 12:
        return "C", "maj"

    chroma = np.array(global_chroma_vector, dtype=float)
    norm = np.linalg.norm(chroma)
    if norm <= 1e-9:
        return "C", "maj"

    chroma_norm = chroma / norm
    best_corr = -1.0
    best_key = ("C", "maj")

    for i, root in enumerate(PITCHES):
        # Major key profile shift
        maj_p = np.roll(MAJOR_PROFILE, i)
        maj_p = maj_p / np.linalg.norm(maj_p)
        corr_maj = float(np.dot(chroma_norm, maj_p))
        if corr_maj > best_corr:
            best_corr = corr_maj
            best_key = (root, "maj")

        # Minor key profile shift
        min_p = np.roll(MINOR_PROFILE, i)
        min_p = min_p / np.linalg.norm(min_p)
        corr_min = float(np.dot(chroma_norm, min_p))
        if corr_min > best_corr:
            best_corr = corr_min
            best_key = (root, "min")

    return best_key


def get_diatonic_chords(root: str, mode: str) -> set[str]:
    """Return set of diatonic major and minor triad chord labels for a given key.

    Parameters
    ----------
    root : str
        Tonic root note e.g. "C", "A", "D#".
    mode : str
        Key mode: "maj" or "min".

    Returns
    -------
    set[str]
        Set of diatonic chord labels e.g. {"C", "Dm", "Em", "F", "G", "Am"}.
    """
    if root not in PITCHES:
        return set()

    root_idx = PITCHES.index(root)
    if mode == "maj":
        # Diatonic triads in Major scale: I (maj), ii (min), iii (min), IV (maj), V (maj), vi (min)
        offsets = [(0, ""), (2, "m"), (4, "m"), (5, ""), (7, ""), (9, "m")]
    else:
        # Diatonic triads in Natural Minor scale: i (min), III (maj), iv (min), v (min), VI (maj), VII (maj)
        offsets = [(0, "m"), (3, ""), (5, "m"), (7, "m"), (8, ""), (10, "")]

    return {f"{PITCHES[(root_idx + off) % 12]}{suffix}" for off, suffix in offsets}
