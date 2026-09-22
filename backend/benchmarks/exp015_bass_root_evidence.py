"""Experiment 015: Bass / Root Evidence Prior.

Tests whether low-register pitch evidence can reduce root-vs-fifth confusion
without changing production detector code.

Configurations:
- Baseline: current production detector.
- Bass-aware: production chroma + beat segmentation + soft root bonus from
  low-register CQT chroma.

Run from backend/:
    python benchmarks/exp015_bass_root_evidence.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.audio.beats import detect_beats
from app.audio.features import extract_chroma_features
from app.audio.models import BeatMap, FeatureSet
from app.chords.classifier import cosine_similarity, normalize_chroma
from app.chords.detector import ChordDetector, build_boundaries, mean_vector
from app.chords.evaluation import evaluate, load_annotations
from app.chords.key_estimation import estimate_key, get_diatonic_chords
from app.chords.models import ChordEvent
from app.chords.smoothing import smooth_predictions
from app.chords.templates import CHORD_TEMPLATES, PITCH_CLASSES
from app.core.config import Settings


SONGS = [
    {
        "name": "Rock Backing Track (C Major)",
        "ann": Path("benchmarks/annotations/rock_backing_c_major.json"),
        "wav": Path("data/processed/fast_rock_backing_c_major/normalized.wav"),
    },
    {
        "name": "Chay Ngay Di (ONIONN Remix)",
        "ann": Path("benchmarks/annotations/chay_ngay_di.json"),
        "wav": Path("data/processed/fast_chay_ngay_di/normalized.wav"),
    },
    {
        "name": "Neu Nhu Ta Chang Con (MCK)",
        "ann": Path("benchmarks/annotations/neu_nhu_ta_chang_con.json"),
        "wav": Path("data/processed/fast_neu_nhu_ta_chang_con/normalized.wav"),
    },
]

CONFUSION_PAIRS = [
    ("C", "F"),
    ("Dm", "Gm"),
    ("Am", "C"),
    ("C", "Am"),
]


def extract_low_register_chroma(audio_path: Path, settings: Settings) -> FeatureSet:
    """Extract C1-B3 chroma from the raw signal as bass/root evidence."""
    hop_length = 2048
    y, sample_rate = librosa.load(str(audio_path), sr=settings.internal_sample_rate, mono=True)

    cqt = np.abs(
        librosa.cqt(
            y=y,
            sr=sample_rate,
            hop_length=hop_length,
            fmin=librosa.note_to_hz("C1"),
            n_bins=36,
            bins_per_octave=12,
        )
    )
    cqt = np.nan_to_num(cqt, nan=0.0, posinf=0.0, neginf=0.0)

    bass_chroma = np.zeros((12, cqt.shape[1]), dtype=float)
    for bin_index in range(cqt.shape[0]):
        pitch_class = bin_index % 12
        octave_index = bin_index // 12
        octave_weight = 1.0 / (1.0 + (octave_index * 0.25))
        bass_chroma[pitch_class] += cqt[bin_index] * octave_weight

    bass_chroma = np.log1p(bass_chroma)
    timestamps = librosa.frames_to_time(
        range(bass_chroma.shape[1]),
        sr=sample_rate,
        hop_length=hop_length,
    )

    return FeatureSet(
        chroma=bass_chroma.T.astype(float).tolist(),
        timestamps=[float(value) for value in timestamps],
        sample_rate=int(sample_rate),
        hop_length=hop_length,
        duration=float(librosa.get_duration(y=y, sr=sample_rate)),
    )


def root_index_for_label(label: str) -> int:
    root = label[:-1] if label.endswith("m") else label
    return PITCH_CLASSES.index(root)


def bass_clarity(bass_chroma: list[float]) -> float:
    normalized = normalize_chroma(bass_chroma)
    ordered = sorted(normalized, reverse=True)
    if not ordered:
        return 0.0
    second = ordered[1] if len(ordered) > 1 else 0.0
    return ordered[0] - second


def classify_bass_aware(
    chroma_vector: list[float],
    bass_chroma_vector: list[float],
    *,
    diatonic_chords: set[str],
    root_bonus_weight: float,
    min_bass_clarity: float,
) -> tuple[str, float]:
    if len(chroma_vector) != 12 or len(bass_chroma_vector) != 12:
        return "N", 0.0

    chroma = normalize_chroma(chroma_vector)
    if max(chroma, default=0.0) <= 0.001:
        return "N", 0.0

    bass_chroma = normalize_chroma(bass_chroma_vector)
    clarity = bass_clarity(bass_chroma_vector)
    use_bass_prior = max(bass_chroma_vector, default=0.0) > 0.001 and clarity >= min_bass_clarity

    scored: list[tuple[str, float]] = []
    for label, template in CHORD_TEMPLATES.items():
        score = cosine_similarity(chroma, template)

        if label in diatonic_chords:
            score += 0.06

        if use_bass_prior:
            score += root_bonus_weight * bass_chroma[root_index_for_label(label)]

        scored.append((label, score))

    scored.sort(key=lambda item: item[1], reverse=True)

    best_label, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0
    margin = best_score - second_score

    if best_score < 0.15:
        return "N", max(0.0, min(1.0, best_score))

    confidence = (best_score * 0.75) + (margin * 1.5)
    return best_label, max(0.0, min(1.0, confidence))


def segment_pair_features(
    features: FeatureSet,
    bass_features: FeatureSet,
    beat_map: BeatMap,
) -> list[dict]:
    boundaries = build_boundaries(features.duration, beat_map)
    chroma_timestamps = np.array(features.timestamps)
    bass_timestamps = np.array(bass_features.timestamps)
    chroma_mat = np.array(features.chroma)
    bass_mat = np.array(bass_features.chroma)

    segments = []
    for start, end in zip(boundaries, boundaries[1:]):
        chroma_idxs = np.where((chroma_timestamps >= start) & (chroma_timestamps < end))[0]
        bass_idxs = np.where((bass_timestamps >= start) & (bass_timestamps < end))[0]

        if len(chroma_idxs) == 0 or len(bass_idxs) == 0:
            continue

        segments.append(
            {
                "start": start,
                "chroma": mean_vector(chroma_mat[chroma_idxs].tolist()),
                "bass_chroma": mean_vector(bass_mat[bass_idxs].tolist()),
            }
        )

    return segments


def detect_bass_aware(
    features: FeatureSet,
    bass_features: FeatureSet,
    beat_map: BeatMap,
    *,
    root_bonus_weight: float,
    min_bass_clarity: float,
) -> list[ChordEvent]:
    global_chroma = mean_vector(features.chroma) if features.chroma else [0.0] * 12
    key_root, key_mode = estimate_key(global_chroma)
    diatonic_chords = get_diatonic_chords(key_root, key_mode)

    labels: list[str] = []
    confidences: list[float] = []
    timestamps: list[float] = []

    for segment in segment_pair_features(features, bass_features, beat_map):
        label, confidence = classify_bass_aware(
            segment["chroma"],
            segment["bass_chroma"],
            diatonic_chords=diatonic_chords,
            root_bonus_weight=root_bonus_weight,
            min_bass_clarity=min_bass_clarity,
        )
        labels.append(label)
        confidences.append(confidence)
        timestamps.append(segment["start"])

    return smooth_predictions(
        labels,
        confidences,
        timestamps,
        features.duration,
        beat_map,
        window_size=1,
        minimum_duration=0.8,
    )


def confusion_seconds(result, pred: str, actual: str) -> float:
    return result.confusion.get((pred, actual), 0.0)


def run_song(song: dict, settings: Settings):
    wav_path = song["wav"]
    ann_path = song["ann"]
    if not wav_path.exists() or not ann_path.exists():
        print(f"SKIP: missing files for {song['name']}")
        return None

    y, sample_rate = sf.read(str(wav_path))
    duration = float(len(y) / sample_rate)
    annotations = load_annotations(ann_path)

    features = extract_chroma_features(wav_path, settings)
    bass_features = extract_low_register_chroma(wav_path, settings)
    beat_map = detect_beats(wav_path, settings)

    baseline_events = ChordDetector().detect(features, beat_map)
    baseline = evaluate(baseline_events, annotations, duration)

    grid = []
    for root_bonus_weight in [0.00, 0.04, 0.08, 0.12, 0.16]:
        for min_bass_clarity in [0.05, 0.10, 0.15, 0.20]:
            events = detect_bass_aware(
                features,
                bass_features,
                beat_map,
                root_bonus_weight=root_bonus_weight,
                min_bass_clarity=min_bass_clarity,
            )
            result = evaluate(events, annotations, duration)
            grid.append((root_bonus_weight, min_bass_clarity, result, events))

    best = max(grid, key=lambda item: item[2].csr_majmin)
    return baseline, best, grid


def format_confusion_pair_summary(result) -> str:
    parts = []
    for pred, actual in CONFUSION_PAIRS:
        seconds = confusion_seconds(result, pred, actual)
        parts.append(f"{actual}->{pred}: {seconds:.2f}s")
    return " | ".join(parts)


def main() -> None:
    settings = Settings()
    all_results = {}

    print("=" * 78)
    print("  EXPERIMENT 015: BASS / ROOT EVIDENCE PRIOR")
    print("=" * 78)

    for song in SONGS:
        print(f"\n{'=' * 78}")
        print(f"SONG: {song['name']}")
        print(f"{'=' * 78}")

        output = run_song(song, settings)
        if output is None:
            continue

        baseline, best, grid = output
        best_weight, best_clarity, best_result, _ = best
        all_results[song["name"]] = {
            "baseline": baseline,
            "best": best_result,
            "weight": best_weight,
            "clarity": best_clarity,
        }

        print(
            "Baseline production : "
            f"CSR={baseline.csr_majmin * 100:5.1f}% | "
            f"Root={baseline.csr_root * 100:5.1f}% | "
            f"{format_confusion_pair_summary(baseline)}"
        )
        print(
            "Best bass-aware     : "
            f"CSR={best_result.csr_majmin * 100:5.1f}% | "
            f"Root={best_result.csr_root * 100:5.1f}% | "
            f"bonus={best_weight:.2f} clarity>={best_clarity:.2f} | "
            f"{format_confusion_pair_summary(best_result)}"
        )

        print("\nTop 5 configs:")
        ranked = sorted(grid, key=lambda item: item[2].csr_majmin, reverse=True)[:5]
        for weight, clarity, result, _ in ranked:
            delta = (result.csr_majmin - baseline.csr_majmin) * 100
            print(
                f"  bonus={weight:.2f} clarity>={clarity:.2f} "
                f"CSR={result.csr_majmin * 100:5.1f}% "
                f"delta={delta:+5.1f}pp"
            )

    if not all_results:
        print("\nNo benchmark files were available.")
        return

    avg_baseline = np.mean([item["baseline"].csr_majmin for item in all_results.values()]) * 100
    avg_best = np.mean([item["best"].csr_majmin for item in all_results.values()]) * 100

    print(f"\n{'=' * 78}")
    print("OVERALL SUMMARY")
    print(f"{'=' * 78}")
    print(f"{'Song':<35} {'Base':>8} {'Bass-aware':>12} {'Delta':>8} {'Best params':>20}")
    print("-" * 78)
    for name, item in all_results.items():
        base = item["baseline"].csr_majmin * 100
        best = item["best"].csr_majmin * 100
        print(
            f"{name:<35} {base:>7.1f}% {best:>11.1f}% "
            f"{best - base:>+7.1f}pp "
            f"b={item['weight']:.2f}, c={item['clarity']:.2f}"
        )
    print("-" * 78)
    print(f"{'AVERAGE':<35} {avg_baseline:>7.1f}% {avg_best:>11.1f}% {avg_best - avg_baseline:>+7.1f}pp")

    if avg_best >= avg_baseline + 5.0:
        print("\nDecision: promising. Consider a production PR after reviewing per-song regressions.")
    else:
        print("\nDecision: weak or plateau. Keep as experiment evidence; do not productionize yet.")


if __name__ == "__main__":
    main()
