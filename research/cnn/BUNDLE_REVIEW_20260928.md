# Review bundle Kaggle 2026-09-28

Source: `D:\chord_cnn_bundle.zip`. Extracted under
`research/cnn/data/trained_bundle_20260928/` (Git-ignored).
ZIP CRC check passed. Exported `chord_cnn.py` exactly matches the local module.

## Reported training and evaluation

- Full run (`smoke_test=false`), 15 epochs; best validation-loss checkpoint: epoch 9.
- At epoch 9: train accuracy 69.31%, validation accuracy 41.38%.
- At epoch 15: train accuracy 74.99%, validation accuracy 39.98%.
- Test window accuracy: 48.87%; root accuracy: 55.37%.
- Macro-F1 over all 24 classes: 0.3818. Four classes have zero test support:
  C:min, D#:min, F#:min, A:min. Their zero F1 is not evidence they all fail.
- Test coverage: 9,948 / 17,256 centers = 57.65%. Unsupported chord labels and
  unannotated centers are not scored. This is not whole-song CSR.
- All 24 classes have training examples, according to the report.
- Training-majority constant baseline: 3.92% on this test distribution.

Training improves while validation stalls/deteriorates: consistent with
overfitting and/or the held-out-group distribution gap, not evidence that
more epochs alone will solve performance.

## Limits and next validation

These values are read from the supplied JSON reports, not independently
recomputed. Do not directly compare this GuitarSet score to existing DSP
scores on different songs or label policies. The model has no no-chord/silence
class, and full mixed-song performance remains unverified.

Next: load checkpoint with `weights_only=True`, run a bounded CPU audio test,
and then compare CNN and DSP on the same annotated recordings and label policy.
At initial inspection local research dependencies were absent; `.venv` at the
repository root could not resolve its configured original Python executable.
A separate `research/cnn/.venv` was created for inference dependencies.
Production detector and backend dependencies have not been changed.

## Local environment blocker

PyTorch 2.10.0+cpu installed in the separate research venv. Installing the audio
dependencies then failed with `OSError: [Errno 28] No space left on device`.
Drive C had approximately 94 MiB free; D had approximately 114 GiB free.
Audio dependency installation is incomplete; do not treat this venv as ready.
No real-audio inference or current DSP comparison has run. The prepared runner
`check_trained_bundle.py` is not yet executed. Use a separate environment on D
before continuing, or free disk space intentionally. No user files were deleted.

## Follow-up: D-drive environment verified

- Created `D:\chord-cnn-env`; installed PyTorch 2.10.0+cpu, numpy 2.0.2,
  librosa 0.11.0 and soundfile 0.13.1 plus dependencies. `pip check` passed.
- CPU checkpoint load and finite-logit forward passed. Labels and config match.
- Real-audio inference passed on seconds 10–40 of the rock benchmark, using
  two PyTorch CPU threads. Temp, Numba cache and results are on D.
- First inference call: 58.79 seconds, including library/JIT initialization;
  this is not a warmed-up latency measurement.
- Reference match: 17.66 / 30 seconds (58.87%). The reference was generated
  from presumed progression/tempo, not independently hand-verified. This short
  crop does not establish full-song accuracy or superiority over current DSP.
- Report: `D:\chord-cnn-results\rock_10_40\report.json`.
- Re-run from project root: `.\research\cnn\run_cpu_check.ps1`.
- Project stays on C; the incomplete research venv there was not removed.
  The D-drive venv references the desktop runtime base Python; recreate it
  with standalone Windows Python if that base installation is removed.
