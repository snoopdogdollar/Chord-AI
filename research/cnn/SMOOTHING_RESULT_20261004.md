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

78 window-center predictions changed. Fewer switches is a stability measurement,
not a measured improvement in overall chord accuracy. The user identified Am
in the focus region; no independent full-track annotations/listening check were
performed. The short wrong A:maj at the beginning of Am remains.

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
