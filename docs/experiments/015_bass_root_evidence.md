# Experiment 015: Bass / Root Evidence Prior

## Hypothesis

Experiment 014 showed that temporal segmentation alone is not the dominant bottleneck. The recurring detector errors are root-function errors, especially:

- Ground truth `F` predicted as `C`
- Ground truth `Gm` predicted as `Dm`
- Relative major/minor confusions such as `C` and `Am`

These pairs share multiple pitch classes. Template matching on full-range chroma cannot reliably tell whether a strong pitch class is the chord root or a supporting fifth/harmonic.

Hypothesis:

If we extract a low-register CQT chroma feature and apply a soft bonus to chord candidates whose root is supported by clear bass evidence, root-vs-fifth confusion should decrease without changing segmentation.

## Implementation

This experiment is implemented as a separate benchmark script only:

```powershell
cd backend
python benchmarks/exp015_bass_root_evidence.py
```

No production detector code is modified.

The script compares:

1. **Baseline production**: `extract_chroma_features` -> `detect_beats` -> `ChordDetector`
2. **Bass-aware variant**:
   - Uses the same production chroma and beat segmentation
   - Extracts low-register CQT chroma from `C1` through `B3`
   - Aggregates bass chroma per beat segment
   - Applies a soft root bonus:

```text
score = cosine_score + diatonic_bonus + root_bonus_weight * bass_chroma[root]
```

The bass prior is only active when the bass chroma has enough clarity:

```text
top_bass_pitch_class - second_bass_pitch_class >= min_bass_clarity
```

The script grid-searches:

```text
root_bonus_weight in [0.00, 0.04, 0.08, 0.12, 0.16]
min_bass_clarity in [0.05, 0.10, 0.15, 0.20]
```

## Acceptance Criteria

This experiment should only be considered for production if it satisfies all of the following:

1. Average CSR improves by at least +5.0pp over current production baseline.
2. Rock Backing Track improves meaningfully, because its ground truth is currently the most reliable.
3. Targeted confusion durations decrease, especially:
   - `F -> C`
   - `Gm -> Dm`
   - `C <-> Am`
4. No single benchmark song regresses severely.
5. Backend tests still pass after any later production refactor.

## Current Status

Implemented, awaiting benchmark run on the local processed audio files.

Results should be recorded here after running the script.

## Production Decision Rule

If the result looks like:

```text
29.9% -> 35%+
```

then the bass/root evidence prior is promising and should be refactored into production behind a small, tested API change.

If the result looks like:

```text
29.9% -> 31%
```

then template matching is probably plateauing, and this should remain experiment evidence rather than production logic.
