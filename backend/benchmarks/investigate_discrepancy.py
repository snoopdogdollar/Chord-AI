"""Reproducibility & Discrepancy Investigation Script.

Compares the 69.6% experiment 011 setup against the current production pipeline setup
for Rock Backing Track (C Major) step by step.
"""

import json
import math
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.audio.beats import detect_beats
from app.audio.features import extract_chroma_features
from app.chords.classifier import classify_chroma, cosine_similarity, normalize_chroma
from app.chords.detector import ChordDetector, mean_vector, median_vector
from app.chords.evaluation import evaluate, load_annotations
from app.chords.key_estimation import estimate_key, get_diatonic_chords
from app.chords.models import ChordEvent
from app.core.config import Settings

PITCHES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

def build_custom_templates(w_root=1.0, w_third=0.85, w_fifth=0.50):
    templates = {}
    qualities = {
        "": [(0, w_root), (4, w_third), (7, w_fifth)],
        "m": [(0, w_root), (3, w_third), (7, w_fifth)]
    }
    for r_idx, root in enumerate(PITCHES):
        for suffix, intervals in qualities.items():
            vec = np.zeros(12)
            for interval, base_w in intervals:
                vec[(r_idx + interval) % 12] = base_w
            templates[f"{root}{suffix}"] = (vec / np.linalg.norm(vec)).tolist()
    return templates


def run_exp011_pipeline(wav_path, ann_path):
    """Exact pipeline used in Experiment 011 (Task 754)."""
    y, sr = sf.read(str(wav_path))
    duration = float(len(y) / sr)

    # Raw CQT chroma without HPSS
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)
    chroma = np.nan_to_num(chroma, nan=0.0, posinf=0.0, neginf=0.0)
    chroma = np.log1p(1.0 * chroma).T.tolist()

    annotations = load_annotations(ann_path)

    global_c = np.mean(chroma, axis=0).tolist()
    k_root, k_mode = estimate_key(global_c)
    diatonic = get_diatonic_chords(k_root, k_mode)

    # Fixed 2.4s synthetic bar grid starting at 10.0s
    beats = list(np.arange(10.0, duration, 2.4))
    timestamps = [i * 2048 / sr for i in range(len(chroma))]
    chroma_mat = np.array(chroma)

    tmpls = build_custom_templates(1.0, 0.85, 0.50)
    events = []
    for i in range(len(beats) - 1):
        b_start, b_end = beats[i], beats[i + 1]
        idxs = np.where((np.array(timestamps) >= b_start) & (np.array(timestamps) < b_end))[0]
        if len(idxs) == 0:
            continue
        avg_c = np.mean(chroma_mat[idxs], axis=0).tolist()
        peak = max(avg_c, default=0.0)
        norm_c = [v / peak if peak > 0.001 else 0.0 for v in avg_c]

        scored = []
        for label, tmpl in tmpls.items():
            score = cosine_similarity(norm_c, tmpl)
            if label in diatonic:
                score += 0.06
            scored.append((label, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        events.append(ChordEvent(start=b_start, end=b_end, chord=scored[0][0], confidence=scored[0][1]))

    res = evaluate(events, annotations, duration)
    return res, events


def run_production_pipeline(wav_path, ann_path, settings):
    """Current production pipeline."""
    y, sr = sf.read(str(wav_path))
    duration = float(len(y) / sr)

    features = extract_chroma_features(wav_path, settings)
    beats = detect_beats(wav_path, settings)
    events = ChordDetector().detect(features, beats)
    annotations = load_annotations(ann_path)

    res = evaluate(events, annotations, duration)
    return res, events, features, beats


def main():
    settings = Settings()
    wav_path = Path("data/processed/fast_rock_backing_c_major/normalized.wav")
    ann_path = Path("benchmarks/annotations/rock_backing_c_major.json")

    print("=" * 70)
    print("REPRODUCIBILITY INVESTIGATION REPORT")
    print("=" * 70)

    # 1. Run Exp 011 exact script
    res_011, events_011 = run_exp011_pipeline(wav_path, ann_path)
    print(f"\n1. Exp 011 Pipeline CSR:        {res_011.csr_majmin*100:.2f}% (Root: {res_011.csr_root*100:.2f}%)")

    # 2. Run Production pipeline
    res_prod, events_prod, features_prod, beats_prod = run_production_pipeline(wav_path, ann_path, settings)
    print(f"2. Current Production CSR:     {res_prod.csr_majmin*100:.2f}% (Root: {res_prod.csr_root*100:.2f}%)")

    # Now step by step isolate the differences between 1 and 2!

    # A. HPSS Impact
    # Exp 011 chroma without HPSS vs Production chroma with HPSS
    y, sr = sf.read(str(wav_path))
    duration = float(len(y) / sr)

    chroma_raw = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)
    chroma_raw = np.log1p(1.0 * np.nan_to_num(chroma_raw, nan=0.0)).T.tolist()

    harmonic, _ = librosa.effects.hpss(y)
    chroma_hpss = librosa.feature.chroma_cqt(y=harmonic, sr=sr, hop_length=2048)
    chroma_hpss = np.log1p(1.0 * np.nan_to_num(chroma_hpss, nan=0.0)).T.tolist()

    print("\n--- A. HPSS DIFFERENCE TEST ---")
    # Evaluate Exp 011 with HPSS chroma
    beats_011 = list(np.arange(10.0, duration, 2.4))
    timestamps_011 = [i * 2048 / sr for i in range(len(chroma_hpss))]
    chroma_mat_hpss = np.array(chroma_hpss)
    annotations = load_annotations(ann_path)

    global_c_hpss = np.mean(chroma_hpss, axis=0).tolist()
    k_root_hpss, k_mode_hpss = estimate_key(global_c_hpss)
    diatonic_hpss = get_diatonic_chords(k_root_hpss, k_mode_hpss)

    tmpls = build_custom_templates(1.0, 0.85, 0.50)
    events_hpss = []
    for i in range(len(beats_011) - 1):
        b_start, b_end = beats_011[i], beats_011[i + 1]
        idxs = np.where((np.array(timestamps_011) >= b_start) & (np.array(timestamps_011) < b_end))[0]
        if len(idxs) == 0:
            continue
        avg_c = np.mean(chroma_mat_hpss[idxs], axis=0).tolist()
        peak = max(avg_c, default=0.0)
        norm_c = [v / peak if peak > 0.001 else 0.0 for v in avg_c]

        scored = []
        for label, tmpl in tmpls.items():
            score = cosine_similarity(norm_c, tmpl)
            if label in diatonic_hpss:
                score += 0.06
            scored.append((label, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        events_hpss.append(ChordEvent(start=b_start, end=b_end, chord=scored[0][0], confidence=scored[0][1]))

    res_hpss = evaluate(events_hpss, annotations, duration)
    print(f"Exp 011 WITH HPSS:              {res_hpss.csr_majmin*100:.2f}% (Key detected: {k_root_hpss} {k_mode_hpss})")

    print("\n--- B. SEGMENTATION / BEAT GRID DIFFERENCE TEST ---")
    # What happens when we use librosa detected beats instead of fixed 2.4s grid?
    detected_beats = beats_prod.beats
    # Evaluate Exp 011 logic using detected beats
    events_det_beats = []
    beat_boundaries = [0.0] + [b for b in detected_beats if 0.0 < b < duration] + [duration]
    for b_start, b_end in zip(beat_boundaries, beat_boundaries[1:]):
        idxs = np.where((np.array(timestamps_011) >= b_start) & (np.array(timestamps_011) < b_end))[0]
        if len(idxs) == 0:
            continue
        avg_c = np.mean(chroma_mat_hpss[idxs], axis=0).tolist()
        peak = max(avg_c, default=0.0)
        norm_c = [v / peak if peak > 0.001 else 0.0 for v in avg_c]

        scored = []
        for label, tmpl in tmpls.items():
            score = cosine_similarity(norm_c, tmpl)
            if label in diatonic_hpss:
                score += 0.06
            scored.append((label, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        events_det_beats.append(ChordEvent(start=b_start, end=b_end, chord=scored[0][0], confidence=scored[0][1]))

    res_det_beats = evaluate(events_det_beats, annotations, duration)
    print(f"Exp 011 WITH Librosa Beat Track:{res_det_beats.csr_majmin*100:.2f}% (BPM={beats_prod.bpm:.1f}, {len(detected_beats)} beats)")

    print("\n--- C. SMOOTHING / MERGING DIFFERENCE TEST ---")
    # What happens if we apply smooth_predictions on events_det_beats?
    from app.chords.smoothing import smooth_predictions
    labels_db = [e.chord for e in events_det_beats]
    confs_db = [e.confidence for e in events_det_beats]
    ts_db = [e.start for e in events_det_beats]
    smoothed_events = smooth_predictions(labels_db, confs_db, ts_db, duration, beats_prod, window_size=1, minimum_duration=0.8)
    res_smoothed = evaluate(smoothed_events, annotations, duration)
    print(f"Exp 011 + Librosa Beats + Smoothing: {res_smoothed.csr_majmin*100:.2f}%")


if __name__ == "__main__":
    main()
