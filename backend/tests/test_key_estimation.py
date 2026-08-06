"""Unit tests for Krumhansl-Schmuckler Key Estimation module."""

import pytest
from app.chords.key_estimation import estimate_key, get_diatonic_chords


class TestEstimateKey:
    def test_c_major_profile_estimation(self):
        # Ideal C Major chroma: C, E, G high
        c_major_chroma = [1.0, 0.0, 0.0, 0.0, 0.8, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0]
        root, mode = estimate_key(c_major_chroma)
        assert root in ("C", "A")  # C Major or its relative minor A minor

    def test_empty_chroma_returns_default(self):
        root, mode = estimate_key([0.0] * 12)
        assert root == "C"
        assert mode == "maj"

    def test_invalid_length_returns_default(self):
        root, mode = estimate_key([1.0, 2.0])
        assert root == "C"
        assert mode == "maj"


class TestGetDiatonicChords:
    def test_c_major_diatonic_chords(self):
        chords = get_diatonic_chords("C", "maj")
        expected = {"C", "Dm", "Em", "F", "G", "Am"}
        assert chords == expected

    def test_a_minor_diatonic_chords(self):
        chords = get_diatonic_chords("A", "min")
        expected = {"Am", "C", "Dm", "Em", "F", "G"}
        assert chords == expected

    def test_d_minor_diatonic_chords(self):
        chords = get_diatonic_chords("D", "min")
        expected = {"Dm", "F", "Gm", "Am", "A#", "C"}
        assert chords == expected

    def test_invalid_key_returns_empty(self):
        chords = get_diatonic_chords("X", "maj")
        assert chords == set()
