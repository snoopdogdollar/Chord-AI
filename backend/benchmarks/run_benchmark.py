"""Benchmark runner for chord detection accuracy.

Usage:
    python -m benchmarks.run_benchmark
    python -m benchmarks.run_benchmark --annotation benchmarks/annotations/chay_ngay_di.json --audio benchmarks/audio/chay_ngay_di.mp3

This script:
1. Loads a ground truth annotation JSON file.
2. Runs the full audio pipeline (extraction → normalization → features → beats → detection).
3. Compares predictions against ground truth using mir_eval.
4. Prints a detailed accuracy report.

Requirements:
- Audio file must exist in benchmarks/audio/.
- Annotation file must be filled in (not placeholder).
- mir_eval must be installed: pip install mir_eval
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the backend package is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.audio.pipeline import AudioPipeline
from app.chords.detector import ChordDetector
from app.chords.evaluation import evaluate, format_evaluation_report, load_annotations
from app.core.config import Settings


BENCHMARKS_DIR = Path(__file__).resolve().parent
ANNOTATIONS_DIR = BENCHMARKS_DIR / "annotations"
AUDIO_DIR = BENCHMARKS_DIR / "audio"


def find_audio_file(stem: str) -> Path | None:
    """Find an audio file matching the annotation stem."""
    for ext in (".mp3", ".wav", ".flac", ".m4a"):
        candidate = AUDIO_DIR / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def run_single_benchmark(
    annotation_path: Path,
    audio_path: Path,
    settings: Settings,
    *,
    analysis_start: float | None = None,
    analysis_end: float | None = None,
) -> None:
    """Run a single benchmark: pipeline → detect → evaluate → report."""
    print(f"\n{'=' * 60}")
    print(f"  Benchmark: {annotation_path.stem}")
    print(f"  Audio:     {audio_path}")
    print(f"{'=' * 60}\n")

    # Load ground truth.
    annotations = load_annotations(annotation_path)
    if not annotations or (len(annotations) == 1 and annotations[0].chord == "N"):
        print("  ⚠ Annotation file appears to be a placeholder.")
        print("  ⚠ Please fill in chord data from Hợp Âm Chuẩn before running.")
        print()
        return

    # Run pipeline.
    print("  [1/4] Running audio pipeline...")
    pipeline = AudioPipeline(settings)
    song_id = f"benchmark_{annotation_path.stem}"
    _, features, beat_map = pipeline.run(
        audio_path,
        song_id,
        analysis_start_seconds=analysis_start,
        analysis_end_seconds=analysis_end,
    )

    # Detect chords.
    print("  [2/4] Running chord detector...")
    detector = ChordDetector()
    predicted = detector.detect(features, beat_map)

    # Show predictions.
    print(f"  [3/4] Predicted {len(predicted)} chord events:")
    for event in predicted:
        print(f"         {event.start:>7.2f}s - {event.end:>7.2f}s  {event.chord:<6}  conf={event.confidence:.3f}")
    print()

    # Show ground truth.
    print(f"         Ground truth: {len(annotations)} annotations:")
    for ann in annotations:
        print(f"         {ann.start:>7.2f}s - {ann.end:>7.2f}s  {ann.chord}")
    print()

    # Evaluate.
    print("  [4/4] Computing accuracy metrics...")
    duration = features.duration
    result = evaluate(predicted, annotations, duration)

    # Print report.
    report = format_evaluation_report(result, title=annotation_path.stem)
    print(report)

    # Print confidence distribution.
    if predicted:
        confidences = [e.confidence for e in predicted]
        print("Confidence Distribution")
        print(f"  min    : {min(confidences):.3f}")
        print(f"  max    : {max(confidences):.3f}")
        print(f"  mean   : {sum(confidences) / len(confidences):.3f}")
        below_70 = sum(1 for c in confidences if c < 0.70)
        below_65 = sum(1 for c in confidences if c < 0.65)
        print(f"  < 0.70 : {below_70}/{len(confidences)}")
        print(f"  < 0.65 : {below_65}/{len(confidences)}")
        print()


def run_all_benchmarks(settings: Settings) -> None:
    """Discover and run all benchmarks with matching audio files."""
    annotation_files = sorted(ANNOTATIONS_DIR.glob("*.json"))

    if not annotation_files:
        print("No annotation files found in", ANNOTATIONS_DIR)
        return

    found = 0
    for annotation_path in annotation_files:
        audio_path = find_audio_file(annotation_path.stem)
        if audio_path is None:
            print(f"  ⚠ Skipping {annotation_path.stem}: no audio file found in {AUDIO_DIR}")
            continue
        found += 1
        run_single_benchmark(annotation_path, audio_path, settings)

    if found == 0:
        print()
        print("No benchmarks could run. To set up benchmarks:")
        print(f"  1. Place audio files in: {AUDIO_DIR}")
        print(f"     (named to match annotation files, e.g., chay_ngay_di.mp3)")
        print(f"  2. Fill in chord annotations in: {ANNOTATIONS_DIR}")
        print(f"     (replace placeholder data with real chords from Hợp Âm Chuẩn)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chord detection benchmark runner")
    parser.add_argument(
        "--annotation",
        type=Path,
        help="Path to a specific annotation JSON file. If omitted, runs all benchmarks.",
    )
    parser.add_argument(
        "--audio",
        type=Path,
        help="Path to the audio file. Required if --annotation is specified.",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=None,
        help="Analysis start time in seconds.",
    )
    parser.add_argument(
        "--end",
        type=float,
        default=None,
        help="Analysis end time in seconds.",
    )
    args = parser.parse_args()

    settings = Settings()

    if args.annotation:
        if not args.annotation.exists():
            print(f"Error: Annotation file not found: {args.annotation}")
            sys.exit(1)

        audio_path = args.audio
        if audio_path is None:
            audio_path = find_audio_file(args.annotation.stem)
        if audio_path is None or not audio_path.exists():
            print(f"Error: Audio file not found for {args.annotation.stem}")
            print(f"  Place the audio file in {AUDIO_DIR} or specify --audio")
            sys.exit(1)

        run_single_benchmark(
            args.annotation,
            audio_path,
            settings,
            analysis_start=args.start,
            analysis_end=args.end,
        )
    else:
        run_all_benchmarks(settings)


if __name__ == "__main__":
    main()
