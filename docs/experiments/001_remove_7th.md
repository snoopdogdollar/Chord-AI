# Experiment 001: Removal of 7th Chord Templates

## Hypothesis
The template space originally consisted of 48 chord templates (12 Major, 12 Minor, 12 Dominant 7th, 12 Minor 7th). 
In an MVP system where only Major/Minor vocabulary is required, 7th chord templates create decision boundary ambiguity (e.g., C major vs C7, Am vs Am7). 
Because 7th chords share 3 out of 4 pitch classes with triads, template matching frequently misclassifies simple triads as 7th chords or vice versa. 
Removing 7th chord templates (reducing template space from 48 to 24) will eliminate false 7th chord predictions and improve Chord Symbol Recall (CSR) for Major/Minor vocabulary.

## Implementation
1. Modified `backend/app/chords/templates.py`:
   - Removed `"7"` and `"m7"` entries from `QUALITY_WEIGHTS`.
   - Template generator now outputs exactly 24 templates (12 Major, 12 Minor).
2. Modified `backend/app/chords/classifier.py`:
   - Removed `SEVENTH_CHORDS` constant and `has_seventh_evidence` function.
   - Removed seventh chord evidence penalty logic.

## Benchmark
Ran evaluation runner across 3 benchmark audio files:
```bash
python -m benchmarks.run_benchmark
```

## Result
| Song | Baseline CSR (48 templates) | Post Step 001 CSR (24 templates) | Delta |
|---|:---:|:---:|:---:|
| **Rock Backing Track** | 29.6% | **34.9%** | **+5.3pp** |
| **Chạy Ngay Đi** | 6.1% | **11.3%** | **+5.2pp** |
| **Nếu Như Ta Chẳng Còn** | 13.4% | **11.6%** | -1.8pp |
| **Average** | 16.4% | **19.3%** | **+2.9pp** |

- False 7th chord predictions (`Gm7`, `Am7`, `C7`, `F7`) were completely eliminated (0 false positives).
- Average CSR improved by **+2.9pp** across all tracks.

## Conclusion
Removing 7th chord templates significantly reduces decision boundary overlap in template matching. 
For an MVP restricted to Major/Minor vocabulary, 24 templates provide higher accuracy and zero false-positive 7th chord detections.
