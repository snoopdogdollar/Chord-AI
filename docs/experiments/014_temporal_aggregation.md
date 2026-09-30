# Experiment 014: Temporal Aggregation & Automatic Chord Boundary Detection

## Executive Summary

Experiment 014 evaluated whether automatic chord-boundary detection and segment-level chroma aggregation can bridge the gap between beat-level production and bar-level oracle benchmarks.

Three configurations were evaluated across all 3 benchmark songs without modifying production code:
- **Config A (Baseline Production)**: Per-beat chroma + HPSS + temporal smoothing
- **Config B (Oracle Upper-Bound)**: Ground-Truth segment boundaries + segment-level mean chroma aggregation
- **Config C (Proposed Auto-Segmentation)**: Beat tracking $\rightarrow$ Chroma novelty change detection $\rightarrow$ Segment-level mean chroma $\rightarrow$ Template matching $\rightarrow$ Smoothing

---

## 📊 Benchmark Results Matrix

### Chord Symbol Recall (CSR MajMin Score)

| Song Name | Config A (Baseline Production) | Config B (Oracle GT Boundaries) | Config C (Auto Segmentation) |
|:---|:---:|:---:|:---:|
| **Rock Backing Track (C Major)** | **45.8%** | 34.7% | 45.5% |
| **Chạy Ngay Đi (Sơn Tùng M-TP)** | 30.1% | **36.7%** (+6.6pp) | 24.6% |
| **Nếu Như Ta Chẳng Còn (MCK)** | 13.8% | **16.6%** (+2.8pp) | 11.5% |
| **AVERAGE CSR** | **29.9%** | **29.4%** | **27.2%** |

---

## 📐 Boundary Detection Metrics (Config C vs Ground Truth ±300ms)

| Song Name | Boundary Precision | Boundary Recall | Boundary F1 Score | Pred Segments | Avg Pred Duration | GT Segments | Avg GT Duration |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Rock Backing Track** | 0.0% | 0.0% | 0.0% | 96 | 2.49s | 95 | 2.41s |
| **Chạy Ngay Đi** | 41.2% | 25.2% | 31.2% | 82 | 3.85s | 158 | 1.93s |
| **Nếu Như Ta Chẳng Còn** | 14.1% | 19.1% | 16.2% | 140 | 2.25s | 114 | 2.60s |

---

## 🔍 Detailed Analysis of Findings

### 1. Oracle Upper-Bound (Config B) Insight
- On pop songs (**Chạy Ngay Đi** and **MCK**), knowing the exact chord boundaries improves CSR by **+2.8pp to +6.6pp** (reaching 36.7% on Chạy Ngay Đi).
- However, on **Rock Backing Track**, Oracle GT segmentation under HPSS preprocessing drops to **34.7%** (due to harmonic spectrum distortion from percussive separation causing $F \rightarrow C$ and $G \rightarrow Bm$ bar-level misclassifications).
- Across all 3 songs, Oracle GT segmentation averages **29.4%** vs Production Baseline **29.9%**.

### 2. Automatic Boundary Detection (Config C) Evaluation
- Chroma novelty curves ($1 - \text{cosine}(c_{\text{left}}, c_{\text{right}})$) pick up major section transitions but struggle to pinpoint subtle intra-verse triad changes ($\text{F1} = 16.2\% - 31.2\%$).
- On Rock Backing Track, the steady acoustic rhythm without percussive fills results in a flat novelty curve ($\text{F1} = 0.0\%$), forcing maximum duration constraints ($3.6\text{s}$).

### 3. Key Conclusion: Is Temporal Segmentation the Dominant Bottleneck?
**NO.** 
While temporal segmentation plays a secondary role on pop songs (+6.6pp potential), **the primary ceiling of Template Matching V1 is harmonic pitch-class confusion**:
1. **Root vs. 5th Confusion** ($F \leftrightarrow C$, $Gm \leftrightarrow Dm$)
2. **Relative Major/Minor Confusion** ($C \leftrightarrow Am$)
3. **Bass / Vocal Harmonics Interference**

Template matching cannot distinguish whether a prominent pitch class is a Root vs 5th when acoustic harmonics overlap.
