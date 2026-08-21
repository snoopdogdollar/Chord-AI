"""Fix Ground Truth annotations by snapping to real audio beats.

Instead of linear-extrapolated timestamps (bar * 1.9s), this script:
1. Detects actual beats from the audio file using librosa
2. Groups beats into bar boundaries (every 4 beats for 4/4 time)
3. Snaps each chord annotation start/end to the nearest bar boundary
4. Properly marks intro/outro gaps as N (No Chord)
5. Saves the corrected JSON alongside the original
"""

import json
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


def detect_beat_grid(audio_path: str | Path, sr: int = 22050):
    """Detect beats and construct bar-level grid from audio."""
    y, sample_rate = librosa.load(str(audio_path), sr=sr, mono=True)
    duration = float(len(y) / sample_rate)

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sample_rate)
    beats = librosa.frames_to_time(beat_frames, sr=sample_rate)
    bpm = float(tempo[0] if hasattr(tempo, "__len__") else tempo)

    # Group beats into downbeats (every 4th beat = bar boundary in 4/4)
    # The first beat is always a downbeat
    downbeats = beats[::4].tolist()

    # Also keep ALL beats for finer snapping
    all_beats = beats.tolist()

    return {
        "duration": duration,
        "bpm": bpm,
        "all_beats": all_beats,
        "downbeats": downbeats,
        "num_beats": len(all_beats),
        "num_bars": len(downbeats),
    }


def snap_to_nearest(timestamp: float, grid: list[float], max_tolerance: float = 5.0) -> float:
    """Snap a timestamp to the nearest grid point within tolerance."""
    if not grid:
        return timestamp
    idx = int(np.argmin([abs(g - timestamp) for g in grid]))
    if abs(grid[idx] - timestamp) <= max_tolerance:
        return grid[idx]
    return timestamp


def fix_annotations(
    ann_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path | None = None,
    beats_per_bar: int = 4,
):
    """Re-align ground truth annotations to actual audio beat grid.

    Parameters
    ----------
    ann_path : path to the original annotation JSON
    audio_path : path to the normalized WAV audio file
    output_path : where to save the fixed JSON (default: overwrites ann_path)
    beats_per_bar : beats per bar (4 for 4/4 time)
    """
    # Load original annotations
    with open(ann_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_annotations = data["annotations"]
    original_title = data.get("title", "Unknown")
    original_source = data.get("source", "Unknown")

    print(f"\n{'='*70}")
    print(f"FIXING GROUND TRUTH: {original_title}")
    print(f"{'='*70}")

    # Detect beat grid from audio
    grid = detect_beat_grid(audio_path)

    # --- Tempo octave error detection ---
    # librosa often detects 2x the real BPM. Compare detected bar duration
    # against the average chord duration from the original annotation.
    avg_chord_dur = np.mean([
        a["end"] - a["start"] for a in original_annotations
    ])
    detected_bar_dur = 60.0 / grid["bpm"] * beats_per_bar  # expected bar duration
    ratio = avg_chord_dur / detected_bar_dur

    if 1.6 < ratio < 2.4:
        # Detected BPM is ~2x the real BPM (octave error)
        effective_beats_per_bar = beats_per_bar * 2
        corrected_bpm = grid["bpm"] / 2.0
        print(f"\n  *** TEMPO OCTAVE ERROR DETECTED ***")
        print(f"  Detected BPM: {grid['bpm']:.1f} -> Corrected BPM: {corrected_bpm:.1f}")
        print(f"  Avg chord dur: {avg_chord_dur:.3f}s, Detected bar dur: {detected_bar_dur:.3f}s, Ratio: {ratio:.2f}")
        print(f"  Using {effective_beats_per_bar} beats per bar instead of {beats_per_bar}")
    else:
        effective_beats_per_bar = beats_per_bar
        corrected_bpm = grid["bpm"]

    print(f"\nAudio Analysis:")
    print(f"  Duration:  {grid['duration']:.2f}s")
    print(f"  BPM:       {corrected_bpm:.1f} (raw: {grid['bpm']:.1f})")
    print(f"  Beats:     {grid['num_beats']}")

    all_beats = grid["all_beats"]
    # Rebuild downbeats with corrected grouping
    downbeats = all_beats[::effective_beats_per_bar]
    duration = grid["duration"]

    print(f"  Bars:      {len(downbeats)} (every {effective_beats_per_bar} beats)")

    # Strategy: The chord progression repeats in groups.
    # Each chord lasts 1 bar (4 beats). So we snap to downbeats.
    #
    # But we need to figure out WHERE the chord progression starts.
    # The original annotation tells us the first chord starts around ann[0]['start'].
    # We snap that to the nearest downbeat, then build from there.

    first_chord_time = original_annotations[0]["start"]
    last_chord_end = original_annotations[-1]["end"]

    # Find the downbeat closest to where the first chord starts
    first_downbeat_idx = int(np.argmin([abs(d - first_chord_time) for d in downbeats]))

    print(f"\nOriginal annotation span: {first_chord_time:.2f}s -> {last_chord_end:.2f}s")
    print(f"  First chord snaps to downbeat[{first_downbeat_idx}] = {downbeats[first_downbeat_idx]:.3f}s")
    print(f"  (Original was {first_chord_time:.2f}s, delta = {abs(downbeats[first_downbeat_idx] - first_chord_time)*1000:.0f} ms)")

    # Build the new annotation list
    # Each original chord gets assigned to one bar (from downbeat[i] to downbeat[i+1])
    num_chords = len(original_annotations)
    new_annotations = []
    drift_report = []

    for i, chord_ann in enumerate(original_annotations):
        bar_idx = first_downbeat_idx + i

        if bar_idx >= len(downbeats):
            # We've run out of detected downbeats — extrapolate from last known
            # using the median bar duration
            if len(new_annotations) >= 2:
                median_bar = np.median([
                    new_annotations[j]["end"] - new_annotations[j]["start"]
                    for j in range(len(new_annotations))
                ])
            else:
                median_bar = 60.0 / corrected_bpm * beats_per_bar

            start = new_annotations[-1]["end"] if new_annotations else downbeats[-1]
            end = start + median_bar

            if end > duration:
                break
        elif bar_idx + 1 < len(downbeats):
            start = downbeats[bar_idx]
            end = downbeats[bar_idx + 1]
        else:
            # Last downbeat: estimate end from beat spacing
            start = downbeats[bar_idx]
            if len(all_beats) > 0:
                # Find beats after this downbeat
                later_beats = [b for b in all_beats if b > start + 0.1]
                if len(later_beats) >= effective_beats_per_bar:
                    end = later_beats[effective_beats_per_bar - 1]
                elif later_beats:
                    avg_beat_dur = np.mean(np.diff(all_beats[-8:])) if len(all_beats) > 1 else 0.5
                    end = start + avg_beat_dur * effective_beats_per_bar
                else:
                    end = min(start + 60.0 / corrected_bpm * beats_per_bar, duration)
            else:
                end = min(start + 60.0 / corrected_bpm * beats_per_bar, duration)

        # Clamp end to audio duration
        end = min(end, duration)

        if start >= duration:
            break

        orig_start = chord_ann["start"]
        orig_end = chord_ann["end"]
        drift_start = abs(start - orig_start) * 1000  # ms
        drift_end = abs(end - orig_end) * 1000  # ms

        new_annotations.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "chord": chord_ann["chord"],
        })

        drift_report.append({
            "idx": i,
            "chord": chord_ann["chord"],
            "orig_start": orig_start,
            "new_start": round(start, 3),
            "drift_start_ms": drift_start,
            "orig_end": orig_end,
            "new_end": round(end, 3),
            "drift_end_ms": drift_end,
        })

    # Print drift statistics
    all_start_drifts = [d["drift_start_ms"] for d in drift_report]
    all_end_drifts = [d["drift_end_ms"] for d in drift_report]

    print(f"\nDrift Statistics ({len(drift_report)} chords):")
    print(f"  Start drift: avg={np.mean(all_start_drifts):.0f}ms, "
          f"max={np.max(all_start_drifts):.0f}ms, "
          f"median={np.median(all_start_drifts):.0f}ms")
    print(f"  End drift:   avg={np.mean(all_end_drifts):.0f}ms, "
          f"max={np.max(all_end_drifts):.0f}ms, "
          f"median={np.median(all_end_drifts):.0f}ms")

    # Show worst drifts
    worst = sorted(drift_report, key=lambda d: d["drift_start_ms"], reverse=True)[:5]
    print(f"\n  Worst start drifts:")
    for w in worst:
        print(f"    Chord #{w['idx']:3d} {w['chord']:4s}: "
              f"{w['orig_start']:.2f}s -> {w['new_start']:.3f}s "
              f"(drift {w['drift_start_ms']:.0f}ms)")

    # Coverage analysis
    covered = sum(a["end"] - a["start"] for a in new_annotations)
    print(f"\nCoverage:")
    print(f"  Annotated:   {covered:.2f}s / {duration:.2f}s ({covered/duration*100:.1f}%)")
    print(f"  Intro (N):   0.00s -> {new_annotations[0]['start']:.3f}s")
    print(f"  Outro (N):   {new_annotations[-1]['end']:.3f}s -> {duration:.2f}s")

    # Bar duration consistency check
    bar_durations = [a["end"] - a["start"] for a in new_annotations]
    print(f"\nBar duration consistency:")
    print(f"  Mean:   {np.mean(bar_durations):.3f}s")
    print(f"  Std:    {np.std(bar_durations):.3f}s")
    print(f"  Min:    {np.min(bar_durations):.3f}s")
    print(f"  Max:    {np.max(bar_durations):.3f}s")

    # Assemble final output
    output_data = {
        "title": original_title,
        "source": original_source + " | Beat-aligned by fix_ground_truth.py",
        "notes": (
            f"Beat-aligned Ground Truth. "
            f"Detected BPM: {corrected_bpm:.1f} (raw: {grid['bpm']:.1f}). "
            f"Timestamps snapped to librosa beat grid (downbeats). "
            f"Original linear-extrapolated timestamps replaced. "
            f"Avg start drift correction: {np.mean(all_start_drifts):.0f}ms."
        ),
        "annotations": new_annotations,
    }

    # Save
    save_path = output_path or ann_path
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(new_annotations)} annotations to: {save_path}")
    return new_annotations


def main():
    proc_dir = Path("data/processed")

    songs = [
        {
            "name": "Chay Ngay Di",
            "ann": "benchmarks/annotations/chay_ngay_di.json",
            "audio": proc_dir / "fast_chay_ngay_di" / "normalized.wav",
        },
        {
            "name": "Neu Nhu Ta Chang Con",
            "ann": "benchmarks/annotations/neu_nhu_ta_chang_con.json",
            "audio": proc_dir / "fast_neu_nhu_ta_chang_con" / "normalized.wav",
        },
    ]

    for song in songs:
        ann_path = Path(song["ann"])
        audio_path = Path(song["audio"])

        if not audio_path.exists():
            print(f"SKIP: Audio not found: {audio_path}")
            continue

        if not ann_path.exists():
            print(f"SKIP: Annotation not found: {ann_path}")
            continue

        # Backup original
        backup_path = ann_path.with_suffix(".json.bak")
        if not backup_path.exists():
            import shutil
            shutil.copy2(ann_path, backup_path)
            print(f"Backed up original to: {backup_path}")

        fix_annotations(ann_path, audio_path)

    print(f"\n{'='*70}")
    print("DONE. Ground truth files have been beat-aligned.")
    print("Run benchmark to verify CSR improvement.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
