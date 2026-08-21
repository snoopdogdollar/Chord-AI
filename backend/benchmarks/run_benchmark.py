"""Run benchmark on all 3 songs with the current detector and fixed Ground Truth.

Outputs CSR scores and confusion matrices for comparison.
"""
import sys
from pathlib import Path

import soundfile as sf

from app.audio.beats import detect_beats
from app.audio.features import extract_chroma_features
from app.chords.detector import ChordDetector
from app.chords.evaluation import evaluate, load_annotations, format_evaluation_report
from app.core.config import Settings


def run_benchmark(song_name, ann_path, audio_dir, settings):
    """Run detection + evaluation for a single song."""
    wav_path = audio_dir / "normalized.wav"

    if not wav_path.exists():
        print(f"  SKIP: {wav_path} not found")
        return None

    ann_path = Path(ann_path)
    if not ann_path.exists():
        print(f"  SKIP: {ann_path} not found")
        return None

    # Get audio duration
    y, sr = sf.read(str(wav_path))
    duration = float(len(y) / sr)

    # Run the full detection pipeline
    features = extract_chroma_features(wav_path, settings)
    beats = detect_beats(wav_path, settings)
    events = ChordDetector().detect(features, beats)

    # Load ground truth
    annotations = load_annotations(ann_path)

    # Evaluate
    result = evaluate(events, annotations, duration)

    # Print report
    report = format_evaluation_report(result, title=song_name)
    print(report)

    return result


def main():
    settings = Settings()
    proc_dir = Path("data/processed")

    songs = [
        {
            "name": "Rock Backing Track (C Major)",
            "ann": "benchmarks/annotations/rock_backing_c_major.json",
            "audio_dir": proc_dir / "fast_rock_backing_c_major",
        },
        {
            "name": "Chay Ngay Di (ONIONN Remix)",
            "ann": "benchmarks/annotations/chay_ngay_di.json",
            "audio_dir": proc_dir / "fast_chay_ngay_di",
        },
        {
            "name": "Neu Nhu Ta Chang Con (MCK)",
            "ann": "benchmarks/annotations/neu_nhu_ta_chang_con.json",
            "audio_dir": proc_dir / "fast_neu_nhu_ta_chang_con",
        },
    ]

    print("=" * 70)
    print("  BENCHMARK: POST-GROUND-TRUTH-FIX EVALUATION")
    print("=" * 70)

    results = {}
    for song in songs:
        print(f"\n{'='*70}")
        result = run_benchmark(
            song["name"], song["ann"], song["audio_dir"], settings
        )
        if result:
            results[song["name"]] = result
        print("=" * 70)

    # Summary table
    print(f"\n{'='*70}")
    print("  SUMMARY: CSR MajMin Results")
    print(f"{'='*70}")
    print(f"  {'Song':<35} {'CSR (MajMin)':>12} {'CSR (Root)':>12} {'N-rate':>8}")
    print(f"  {'-'*67}")
    for name, r in results.items():
        print(f"  {name:<35} {r.csr_majmin*100:>11.1f}% {r.csr_root*100:>11.1f}% {r.n_rate*100:>7.1f}%")
    print(f"  {'-'*67}")

    if len(results) > 0:
        avg_csr = sum(r.csr_majmin for r in results.values()) / len(results)
        print(f"  {'AVERAGE':<35} {avg_csr*100:>11.1f}%")


if __name__ == "__main__":
    main()
