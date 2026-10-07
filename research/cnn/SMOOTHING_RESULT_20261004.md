# Probability smoothing trial, 2026-10-04

Audio: `D:\Rock Backing Track C Major  100 BPM  C G Am F  Guitar Backing Track - TGuitar.mp3`

Used the existing epoch-9 checkpoint, unchanged (SHA-256
`1d944d630997b62b1c8b2951c1a470b0457d387da9b623e11d35fecd3e78acb1`).
One CPU inference pass, two threads; full audio duration 239.04 s.
Outputs: `D:\chord-cnn-results\rock_smoothing_20261004`.

Centered mean of all 24 class probabilities over a 0.4 s window, before argmax.
At the current stride (about 0.116 s), this normally includes three centers.
No chord-specific overrides, duration deletion or model retraining.

| Measure | Raw | Smoothed |
|---|---:|---:|
| Segments across whole file | 240 | 187 |
| Segments shorter than 0.3 s | 78 | 37 |
| A:maj at 36.049–36.281 s | Present | Removed |
| Continuous A:min in focus region | Interrupted | 33.959–36.397 s |
| Transition into F:maj | 36.397 s | 36.397 s |
| A:maj at 33.843–33.959 s | Present | Still present |

78 window-center predictions changed. Fewer switches is a stability measurement;
accuracy is measured separately against the reference below. The short A:maj
at 33.843–33.959 s remains wrong (the supplied reference labels this time G).

## Evaluation against the user-designated benchmark

Reference: `backend/benchmarks/annotations/rock_backing_c_major.json`, explicitly
identified by the user as ground truth for this audio. Its 95 intervals cover
10.00–238.95 s, totaling 228.95 s. The intro and unannotated tail are excluded.
No timestamp shift or boundary tolerance was applied. Labels are normalized
consistently, e.g. `Am` = `A:min` and `C` = `C:maj`.

Accuracy here means seconds with the correct root AND major/minor quality,
divided by annotated seconds. It is not segment-count accuracy or the Kaggle
test-set accuracy.

| Evaluated region | Raw | Smoothed |
|---|---:|---:|
| All annotated time (228.95 s) | 56.70% | 57.96% |
| Correct duration | 129.83 s | 132.70 s |
| Focus region, 33–39 s | 82.75% | 86.62% |

Overall improvement: **1.25 percentage points**, or **2.87 additional correctly
labeled seconds**. This is a modest improvement on one song; it does not prove
improvement on unseen songs. This track has already informed smoothing work,
so it is a development benchmark rather than an untouched final test.

The reference places Am at 34.10–36.51 s. Smoothed Am spans 33.959–36.397 s:
the internal A:maj interruption is removed, but transition timing still differs.

Machine-readable results: `research/cnn/data/rock_smoothing_benchmark.json`.
Reproduce with the standard-library-only scorer (no inference or training):

```powershell
python research/cnn/score_smoothing.py --reference backend/benchmarks/annotations/rock_backing_c_major.json --comparison-dir 'D:\chord-cnn-results\rock_smoothing_20261004' --output research/cnn/data/rock_smoothing_benchmark.json
```

## Validation

- 10 tests passed: temporal probability logic, edge cases, label/group helpers,
  notebook syntax and embedded-module consistency.
- Full-song raw JSON equals the user's previous `rock_full_prediction.json`
  exactly, confirming the raw inference behavior is preserved on this input.
- Both timelines are positive-length, contiguous, start at zero and end at
  239.04 s. The same time grid is used for raw and smoothed decoding.
- Elapsed inference/comparison was about 5.21 s in this run (not a cold-start
  benchmark and not directly comparable to the original first-run timing).

Use `run_smoothing_check.ps1 -Audio <path>` for other songs. Do not increase the
window based on this one known segment alone: real short chords may disappear.
The current backend DSP detector is untouched; `predict_audio` defaults to raw
for backward compatibility. Pass `smoothing_seconds=0.4` explicitly to enable it.
