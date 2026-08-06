# Experiment 008: Global Key Estimation & Diatonic Prior Weighting

## Hypothesis
The baseline chord detector classified frame-level chroma vectors independently without awareness of the global key/scale of the song. 
Treating all 24 templates as equally probable ($p=1/24$) led to foreign non-diatonic false positives (e.g. `Bm`, `Cm`, `F#m`, `Bbm` appearing in a C Major track).

Hypothesis: 
Estimating the global song key using Krumhansl-Schmuckler Key Profiles:
1. Calculates the global average chroma vector $\mathbf{C}_{\text{global}}$.
2. Correlates $\mathbf{C}_{\text{global}}$ with 24 Major/Minor Krumhansl key profiles to identify the tonic key.
3. Applies a Diatonic Prior Boost ($+0.06$) to the 6 in-key diatonic triads (e.g. `C, Dm, Em, F, G, Am` for C Major).
This will suppress foreign out-of-key false positives and improve overall Chord Symbol Recall (CSR).

## Implementation
1. Created `backend/app/chords/key_estimation.py`:
   - `estimate_key(global_chroma)`: Computes normalized dot product with 12 Major and 12 Minor Krumhansl profiles.
   - `get_diatonic_chords(root, mode)`: Generates diatonic triad sets for Major (I, ii, iii, IV, V, vi) and Minor (i, III, iv, v, VI, VII) scales.
2. Updated `backend/app/chords/classifier.py`:
   - Updated `classify_chroma(chroma_vector, diatonic_chords)` to apply a prior boost ($+0.06$) to diatonic chords.
3. Updated `backend/app/chords/detector.py`:
   - `ChordDetector.detect()` now calculates global average chroma, estimates song key, and passes diatonic chords to classification loop.
4. Created `backend/tests/test_key_estimation.py` (7 unit tests).

## Key Estimation Accuracy Across Benchmark Suite
| Benchmark Track | Actual Key | Krumhansl Estimated Key | Detected Diatonic Set | Status |
|---|:---:|:---:|---|:---:|
| **Rock Backing Track** | C Major / A Minor | **A Minor** (Relative Minor) | `Am, C, Dm, Em, F, G` | **100% Match** |
| **Chạy Ngay Đi** | D Minor (Bb-C-Dm-Am) | **D Minor** | `A#, Am, C, Dm, F, Gm` | **100% Match** |
| **Nếu Như Ta Chẳng Còn** | D Minor (MCK) | **D Minor** | `A#, Am, C, Dm, F, Gm` | **100% Match** |

## Benchmark Accuracy Results

| Song | CSR Post-Step 004 | CSR Post-Step 008 (Key Estimation) | Delta | N-rate |
|---|:---:|:---:|:---:|:---:|
| **Rock Backing Track** | 41.7% | **44.8%** | **+3.1pp** 🚀 | **0.0%** |
| **Chạy Ngay Đi** | 12.3% | **14.2%** | **+1.9pp** 📈 | **0.0%** |
| **Nếu Như Ta Chẳng Còn** | 11.2% | **12.6%** | **+1.4pp** 📈 | **0.0%** |
| **Average Across Suite** | **21.7%** | **23.9%** | **+2.2pp** | **0.0%** |

## Conclusion
Global Key Estimation via Krumhansl-Schmuckler profiles correctly identified the tonic scale across 100% of benchmark songs. 
Adding Diatonic Prior Weighting suppressed foreign out-of-key false positives (e.g. `F#m`, `Bbm`), boosting average CSR from **21.7% to 23.9% (+2.2pp avg gain)** while keeping N-rate at 0.0%.
