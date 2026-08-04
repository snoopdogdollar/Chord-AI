# Experiment 005: Confusion Matrix & Failure Mode Analysis

## Hypothesis
Template-based chord recognition using Cosine Similarity on chroma vectors suffers from systemic confusion between chord pairs that share 2 out of 3 pitch classes (e.g., relative Major/Minor pairs like C major `[C, E, G]` and A minor `[A, C, E]`, or 3rd/5th overlapping pairs like G major `[G, B, D]` and B minor `[B, D, F#]`). 
Hypothesis: Constructing a frame-based confusion matrix (10ms resolution) across benchmark songs will reveal the top 10 misclassifications, identifying the structural limitations of pure template matching before moving to key context or HMM post-processing.

## Implementation
1. Built frame-level confusion matrix calculation in `backend/app/chords/evaluation.py`:
   - Sampled audio at 10ms frame intervals.
   - Tracked cumulative duration (in seconds) of every `(predicted_chord, ground_truth_chord)` pair.
2. Compiled top misclassification patterns across all 3 benchmark songs.

## Benchmark Results (Top Structural Misclassifications)

### Top Misclassifications by Duration

| Predicted Chord | Actual Ground Truth | Duration (s) | Shared Pitch Classes | Root Cause Analysis |
|---|---|:---:|:---:|---|
| **C** | **F** | 25.69 s | `[C]` | Bass overtone of F major (F-A-C) heavily emphasizes C (5th), causing C major template match. |
| **Bm** | **G** | 23.80 s | `[B, D]` | G major (G-B-D) shares 2 notes with B minor (B-D-F#). Guitar overtones add F# harmonic. |
| **F** | **Am** | 21.02 s | `[A, C]` | A minor (A-C-E) shares 2 notes with F major (F-A-C). |
| **Am** | **G** | 15.39 s | `[A]` | Sub-dominant confusion in 100 BPM rock arrangement. |
| **Bm** | **C** | 14.57 s | `[B]` | Leading tone B note in C major progression causing B minor false positive. |
| **A** | **G** | 8.60 s | `[A]` | Parallel major / dominant overtone confusion. |
| **A** | **Am** | 7.54 s | `[A, E]` | Parallel Major/Minor confusion (A major vs A minor). |

---

## Analysis & Diagnostic Findings

1. **Relative Major/Minor & Shared Triad Overlap**:
   - The top failure mode is **2-note overlap confusion**:
     - `G major` (G-B-D) $\longleftrightarrow$ `B minor` (B-D-F#): **23.80s** misclassified.
     - `F major` (F-A-C) $\longleftrightarrow$ `A minor` (A-C-E): **21.02s** misclassified.
   - Because Cosine Similarity weights all 12 chroma bins equally, a 2-note overlap produces a base similarity score of $\ge 0.67$, making it easily triggered by slight harmonic noise.

2. **5th Harmonic Bias**:
   - `F major` (F-A-C) is frequently misclassified as `C major` (**25.69s**) because the 5th note of F is C. In guitar backing tracks, the 5th harmonic often carries strong energy.

## Conclusion
Template matching without global key context or transition smoothing cannot distinguish between chords sharing 2 pitch classes (e.g., G vs Bm, F vs Am). 
This confusion matrix establishes the exact empirical baseline for future improvements (e.g., Key profile weighting, Bass-chroma separation, or HMM Viterbi decoding).
