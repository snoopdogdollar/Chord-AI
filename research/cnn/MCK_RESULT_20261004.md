# MCK CNN evaluation, 2026-10-04

Audio: `backend/data/uploads/0b8a3cbcecf840d8bf33575153ddc0b4_0005299a6af5469cbfdb16ac6c2405ed_N_u_Nh_Ta_Ch_ng_C_n_-_MCK_-_MCK____Nger.mp3`

Full audio duration: 314.808 s. Existing epoch-9 checkpoint, SHA-256
`1d944d630997b62b1c8b2951c1a470b0457d387da9b623e11d35fecd3e78acb1`.
Single CPU inference pass; unchanged centered probability mean window of 0.4 s.
No retraining or per-song parameter tuning.

Reference: `backend/benchmarks/annotations/neu_nhu_ta_chang_con.json`.
Its metadata says chord labels came from hopamchuan.com (Dm), with timestamps
automatically snapped to detected beats. Manual verification against this upload
has not been established. These scores measure agreement with that repository
benchmark, not independently verified musical correctness.

Scoring covers 5.828–301.932 s (296.104 annotated seconds), excludes unannotated
intro/tail, and requires matching root and major/minor quality. No offset or
boundary tolerance was applied.

| Measure | Raw | Smoothed |
|---|---:|---:|
| Duration accuracy | 5.556% | 5.497% |
| Correct duration | 16.451 s | 16.277 s |
| Full-file segment count | 489 | 368 |
| Full-file segments shorter than 0.3 s | 203 | 70 |

Accuracy change: -0.0588 percentage points (-0.1741 correctly labeled seconds).
Smoothing reduces rapid switching but does not improve benchmark accuracy here.
For comparison, on the previous Rock benchmark it improved 56.70% to 57.96%.
There is no evidence from these two songs that smoothing solves the model's
recognition errors across songs.

The dominant full-file predictions are D:maj (about 79 s), F#:maj (44 s),
A:maj (35 s), C#:maj (29 s), and E:maj (25 s), while the reference primarily
contains G:min, A:maj, D:min, and A#:maj. Only about 0.824 of the reference's
67.315 D:min seconds are correct, with or without smoothing. This is a diagnostic
observation; the cause has not yet been established.

Both outputs were checked for positive, contiguous intervals covering the entire
audio. A second calculation using the union of reference/prediction boundaries
and interval midpoints reproduced the duration-overlap scores.

Outputs:

- `D:/chord-cnn-results/mck_smoothing_20261004/raw.json`
- `D:/chord-cnn-results/mck_smoothing_20261004/smoothed.json`
- `D:/chord-cnn-results/mck_smoothing_20261004/probabilities.npz`
- `D:/chord-cnn-results/mck_smoothing_20261004/comparison.json`
- `research/cnn/data/mck_smoothing_benchmark.json`

Reproduce scoring from the repository root:

```powershell
python -B research/cnn/score_smoothing.py --reference backend/benchmarks/annotations/neu_nhu_ta_chang_con.json --comparison-dir 'D:\chord-cnn-results\mck_smoothing_20261004' --output research/cnn/data/mck_smoothing_benchmark.json
```

Next diagnostic step: verify a short excerpt's chord labels, musical key, and
timing against this exact upload, then inspect model confusions before changing
training or smoothing. Production detection was not changed by this evaluation.
