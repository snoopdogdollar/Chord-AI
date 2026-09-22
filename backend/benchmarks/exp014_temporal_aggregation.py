"""Experiment 014: Temporal Aggregation / Automatic Chord Boundary Detection.

Compares 3 configurations across all benchmark songs:
A. Current production baseline (beat-level chroma + HPSS + smoothing)
B. Oracle upper-bound (Ground Truth chord boundaries + segment-level chroma aggregation)
C. Proposed automatic segmentation (beat tracking -> harmonic change/novelty boundary detection -> segment-level chroma aggregation -> template matching -> smoothing)

Rules:
- Separate benchmark script (does not mutate production code)
- Config C MUST NOT use Ground Truth for boundary detection
- Config C MUST NOT hardcode 2.4s or any song-specific fixed bar duration
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
from app.chords.detector import ChordDetector, mean_vector
from app.chords.evaluation import evaluate, load_annotations, format_evaluation_report
from app.chords.key_estimation import estimate_key, get_diatonic_chords
from app.chords.models import ChordEvent
from app.chords.smoothing import smooth_predictions
from app.chords.templates import CHORD_TEMPLATES
from app.core.config import Settings


# ---------------------------------------------------------------------------
# CONFIG A: Current Production Baseline
# ---------------------------------------------------------------------------
def run_config_a(wav_path: Path, ann_path: Path, settings: Settings, duration: float):
    """Config A: Current Production Pipeline (per-beat + HPSS + smoothing)."""
    features = extract_chroma_features(wav_path, settings)
    beats = detect_beats(wav_path, settings)
    events = ChordDetector().detect(features, beats)
    annotations = load_annotations(ann_path)
    res = evaluate(events, annotations, duration)
    return res, events


# ---------------------------------------------------------------------------
# CONFIG B: Oracle Upper-Bound (Ground Truth boundaries + mean chroma)
# ---------------------------------------------------------------------------
def run_config_b(wav_path: Path, ann_path: Path, settings: Settings, duration: float):
    """Config B: Oracle Upper-Bound (GT intervals used for segment aggregation)."""
    features = extract_chroma_features(wav_path, settings)
    annotations = load_annotations(ann_path)

    # Key estimation from global chroma
    global_c = mean_vector(features.chroma)
    key_root, key_mode = estimate_key(global_c)
    diatonic = get_diatonic_chords(key_root, key_mode)

    events = []
    chroma_mat = np.array(features.chroma)
    timestamps = np.array(features.timestamps)

    for ann in annotations:
        start, end = ann.start, ann.end
        if start >= duration:
            continue
        end = min(end, duration)

        idxs = np.where((timestamps >= start) & (timestamps < end))[0]
        if len(idxs) == 0:
            continue

        segment_chroma = mean_vector(chroma_mat[idxs].tolist())
        label, conf = classify_chroma(segment_chroma, diatonic_chords=diatonic)
        if label != "N":
            events.append(ChordEvent(start=start, end=end, chord=label, confidence=conf))

    res = evaluate(events, annotations, duration)
    return res, events


# ---------------------------------------------------------------------------
# CONFIG C: Automatic Harmonic Change Boundary Detection
# ---------------------------------------------------------------------------
def detect_automatic_boundaries(
    beat_timestamps: list[float],
    beat_chromas: list[list[float]],
    duration: float,
    min_segment_dur: float = 0.8,
    max_segment_dur: float = 3.6,
    novelty_threshold: float = 0.12,
    window_k: int = 2,
) -> list[float]:
    """Detect candidate chord boundary timestamps from beat-synchronous chroma.

    Calculates a moving-window chroma novelty curve:
        Novelty[i] = 1.0 - CosineSimilarity( mean(beat_chroma[i-k:i]), mean(beat_chroma[i:i+k]) )

    Applies peak-picking and min/max duration constraints.
    Returns sorted boundary timestamps starting at 0.0 and ending at duration.
    """
    num_beats = len(beat_chromas)
    if num_beats < 2:
        return [0.0, duration]

    # Compute novelty score for each beat boundary i (between beat i-1 and beat i)
    novelty = np.zeros(num_beats)
    for i in range(1, num_beats):
        left_start = max(0, i - window_k)
        left_end = i
        right_start = i
        right_end = min(num_beats, i + window_k)

        left_mean = mean_vector(beat_chromas[left_start:left_end])
        right_mean = mean_vector(beat_chromas[right_start:right_end])

        sim = cosine_similarity(normalize_chroma(left_mean), normalize_chroma(right_mean))
        novelty[i] = max(0.0, 1.0 - sim)

    # Boundary selection using peak detection and constraints
    boundaries = [0.0]
    last_boundary_time = 0.0

    for i in range(1, num_beats):
        t = beat_timestamps[i]
        dur_since_last = t - last_boundary_time

        # Check if novelty is a local peak and exceeds threshold
        is_peak = (
            novelty[i] >= novelty_threshold
            and (i == 1 or novelty[i] >= novelty[i - 1])
            and (i == num_beats - 1 or novelty[i] >= novelty[i + 1])
        )

        # Force a boundary if max duration is reached
        force_boundary = dur_since_last >= max_segment_dur

        if (is_peak and dur_since_last >= min_segment_dur) or force_boundary:
            boundaries.append(t)
            last_boundary_time = t

    if boundaries[-1] < duration:
        boundaries.append(duration)

    return sorted(set(boundaries))


def run_config_c(
    wav_path: Path,
    ann_path: Path,
    settings: Settings,
    duration: float,
    novelty_threshold: float = 0.12,
    min_segment_dur: float = 0.8,
    max_segment_dur: float = 3.6,
):
    """Config C: Automatic Segmentation Pipeline (Beat tracking -> Novelty boundaries -> Mean chroma -> Template matching -> Smoothing)."""
    features = extract_chroma_features(wav_path, settings)
    beat_map = detect_beats(wav_path, settings)
    annotations = load_annotations(ann_path)

    # Key estimation
    global_c = mean_vector(features.chroma)
    key_root, key_mode = estimate_key(global_c)
    diatonic = get_diatonic_chords(key_root, key_mode)

    # Beat-synchronous chroma calculation
    beat_boundaries = [0.0] + [b for b in beat_map.beats if 0.0 < b < duration] + [duration]
    beat_timestamps = beat_boundaries[:-1]
    chroma_mat = np.array(features.chroma)
    timestamps = np.array(features.timestamps)

    beat_chromas = []
    valid_beat_ts = []

    for b_start, b_end in zip(beat_boundaries, beat_boundaries[1:]):
        idxs = np.where((timestamps >= b_start) & (timestamps < b_end))[0]
        if len(idxs) > 0:
            beat_chromas.append(mean_vector(chroma_mat[idxs].tolist()))
            valid_beat_ts.append(b_start)

    # Detect automatic segment boundaries using chroma novelty
    auto_boundaries = detect_automatic_boundaries(
        valid_beat_ts,
        beat_chromas,
        duration,
        min_segment_dur=min_segment_dur,
        max_segment_dur=max_segment_dur,
        novelty_threshold=novelty_threshold,
    )

    # Aggregate chroma per auto-detected segment
    unmerged_events = []
    for s_start, s_end in zip(auto_boundaries, auto_boundaries[1:]):
        idxs = np.where((timestamps >= s_start) & (timestamps < s_end))[0]
        if len(idxs) == 0:
            continue
        seg_c = mean_vector(chroma_mat[idxs].tolist())
        label, conf = classify_chroma(seg_c, diatonic_chords=diatonic)
        if label != "N":
            unmerged_events.append(ChordEvent(start=s_start, end=s_end, chord=label, confidence=conf))

    # Apply temporal smoothing / merging
    if not unmerged_events:
        return evaluate([], annotations, duration), [], auto_boundaries

    labels = [e.chord for e in unmerged_events]
    confs = [e.confidence for e in unmerged_events]
    ts = [e.start for e in unmerged_events]

    smoothed = smooth_predictions(
        labels, confs, ts, duration, beat_map, window_size=1, minimum_duration=min_segment_dur
    )

    res = evaluate(smoothed, annotations, duration)
    return res, smoothed, auto_boundaries


# ---------------------------------------------------------------------------
# Boundary Detection Evaluation Metrics
# ---------------------------------------------------------------------------
def evaluate_boundary_accuracy(
    predicted_boundaries: list[float],
    gt_annotations: list,
    tolerance: float = 0.30,  # ±300ms window
):
    """Compute Precision, Recall, F1 for predicted segment boundaries against GT boundaries."""
    gt_boundaries = [a.start for a in gt_annotations] + [gt_annotations[-1].end]
    gt_boundaries = sorted(set(gt_boundaries))

    # Exclude end points 0.0 and total duration for boundary precision/recall
    pred_internal = [b for b in predicted_boundaries if b > 1.0]
    gt_internal = [b for b in gt_boundaries if b > 1.0]

    if not pred_internal or not gt_internal:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "matched": 0}

    matched_gt = set()
    tp = 0

    for p in pred_internal:
        closest_gt_idx = int(np.argmin([abs(g - p) for g in gt_internal]))
        closest_gt = gt_internal[closest_gt_idx]
        if abs(closest_gt - p) <= tolerance and closest_gt_idx not in matched_gt:
            tp += 1
            matched_gt.add(closest_gt_idx)

    precision = tp / len(pred_internal) if pred_internal else 0.0
    recall = tp / len(gt_internal) if gt_internal else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "matched": tp,
        "total_pred": len(pred_internal),
        "total_gt": len(gt_internal),
    }


# ---------------------------------------------------------------------------
# Main Experiment Runner
# ---------------------------------------------------------------------------
def main():
    settings = Settings()
    proc_dir = Path("data/processed")

    songs = [
        {
            "name": "Rock Backing Track (C Major)",
            "ann": Path("benchmarks/annotations/rock_backing_c_major.json"),
            "wav": proc_dir / "fast_rock_backing_c_major" / "normalized.wav",
        },
        {
            "name": "Chay Ngay Di (ONIONN Remix)",
            "ann": Path("benchmarks/annotations/chay_ngay_di.json"),
            "wav": proc_dir / "fast_chay_ngay_di" / "normalized.wav",
        },
        {
            "name": "Neu Nhu Ta Chang Con (MCK)",
            "ann": Path("benchmarks/annotations/neu_nhu_ta_chang_con.json"),
            "wav": proc_dir / "fast_neu_nhu_ta_chang_con" / "normalized.wav",
        },
    ]

    print("=" * 75)
    print("  EXPERIMENT 014: TEMPORAL AGGREGATION / AUTOMATIC CHORD BOUNDARY DETECTION")
    print("=" * 75)

    all_results = {}

    for song in songs:
        name = song["name"]
        ann_p = song["ann"]
        wav_p = song["wav"]

        if not wav_p.exists() or not ann_p.exists():
            print(f"SKIP: File missing for {name}")
            continue

        y, sr = sf.read(str(wav_p))
        duration = float(len(y) / sr)
        annotations = load_annotations(ann_p)

        print(f"\n{'='*75}")
        print(f"SONG: {name} (Duration: {duration:.2f}s, GT Chords: {len(annotations)})")
        print(f"{'='*75}")

        # Config A
        res_a, events_a = run_config_a(wav_p, ann_p, settings, duration)

        # Config B
        res_b, events_b = run_config_b(wav_p, ann_p, settings, duration)

        # Config C (Automatic Novelty Boundaries)
        res_c, events_c, auto_bounds_c = run_config_c(
            wav_p,
            ann_p,
            settings,
            duration,
            novelty_threshold=0.12,
            min_segment_dur=0.8,
            max_segment_dur=3.6,
        )

        # Boundary evaluation for C
        b_metrics_c = evaluate_boundary_accuracy(auto_bounds_c, annotations)

        # Segment statistics
        durs_a = [e.end - e.start for e in events_a]
        durs_b = [e.end - e.start for e in events_b]
        durs_c = [e.end - e.start for e in events_c]

        print("\n--- RESULTS SUMMARY ---")
        print(f"Config A (Baseline Production)  : CSR MajMin = {res_a.csr_majmin*100:5.1f}% | Root = {res_a.csr_root*100:5.1f}% | Segs = {len(events_a):3d} | Avg Dur = {np.mean(durs_a):.2f}s")
        print(f"Config B (Oracle GT Boundaries): CSR MajMin = {res_b.csr_majmin*100:5.1f}% | Root = {res_b.csr_root*100:5.1f}% | Segs = {len(events_b):3d} | Avg Dur = {np.mean(durs_b):.2f}s")
        print(f"Config C (Auto Segmentation)   : CSR MajMin = {res_c.csr_majmin*100:5.1f}% | Root = {res_c.csr_root*100:5.1f}% | Segs = {len(events_c):3d} | Avg Dur = {np.mean(durs_c):.2f}s")

        print("\n--- BOUNDARY METRICS (Config C vs Ground Truth boundaries ±300ms) ---")
        print(f"  Precision: {b_metrics_c['precision']*100:.1f}% ({b_metrics_c['matched']}/{b_metrics_c['total_pred']} pred boundaries)")
        print(f"  Recall:    {b_metrics_c['recall']*100:.1f}% ({b_metrics_c['matched']}/{b_metrics_c['total_gt']} GT boundaries)")
        print(f"  F1 Score:  {b_metrics_c['f1']*100:.1f}%")

        all_results[name] = {
            "res_a": res_a,
            "res_b": res_b,
            "res_c": res_c,
            "events_a": events_a,
            "events_b": events_b,
            "events_c": events_c,
            "bounds_c": auto_bounds_c,
            "b_metrics_c": b_metrics_c,
        }

    # Print overall comparison matrix across all 3 songs
    print(f"\n{'='*75}")
    print("  OVERALL COMPARISON MATRIX (CSR MajMin Score)")
    print(f"{'='*75}")
    print(f"  {'Song Name':<32} | {'Config A (Base)':>15} | {'Config B (Oracle)':>17} | {'Config C (Auto)':>15}")
    print(f"  {'-'*72}")
    for name, r in all_results.items():
        csr_a = r["res_a"].csr_majmin * 100
        csr_b = r["res_b"].csr_majmin * 100
        csr_c = r["res_c"].csr_majmin * 100
        print(f"  {name:<32} | {csr_a:14.1f}% | {csr_b:16.1f}% | {csr_c:14.1f}%")
    print(f"  {'-'*72}")

    avg_a = np.mean([r["res_a"].csr_majmin for r in all_results.values()]) * 100
    avg_b = np.mean([r["res_b"].csr_majmin for r in all_results.values()]) * 100
    avg_c = np.mean([r["res_c"].csr_majmin for r in all_results.values()]) * 100
    print(f"  {'AVERAGE CSR':<32} | {avg_a:14.1f}% | {avg_b:16.1f}% | {avg_c:14.1f}%")
    print(f"{'='*75}")


if __name__ == "__main__":
    main()
