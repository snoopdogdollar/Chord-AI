# Chord AI — Research & Experimentation Log

This directory contains the documented experimental history of algorithmic changes made to the Chord AI DSP & classification pipeline.
All experiments follow the structured framework: **Hypothesis → Implementation → Benchmark → Result → Conclusion**.

---

## Experiment Index

| ID | Title | Primary Target | Key Metric Impact | Document Link |
|---|---|---|---|---|
| **001** | Removal of 7th Chord Templates | Template Space Reduction | CSR +2.9pp avg, 0% 7th false positives | [001_remove_7th.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/001_remove_7th.md) |
| **002** | Removal of Non-Chord Penalty | Template Matching Stability | Stabilized triad matching | [002_remove_penalty.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/002_remove_penalty.md) |
| **003** | Log Dynamic Range Compression | Feature Extraction | CSR +0.5pp ($\gamma=1.0$) | [003_log_compression.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/003_log_compression.md) |
| **004** | Threshold & Noise Tuning | Classification Thresholds | CSR 29.6% → 41.7%, N-rate 24.2% → 0% | [004_threshold.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/004_threshold.md) |
| **005** | Confusion Matrix Analysis | Error Mode Diagnosis | Identified 2-note pitch overlap failure modes | [005_confusion_matrix.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/005_confusion_matrix.md) |
| **006** | Ablation Study Summary | Component Contribution | Visualized incremental CSR gains per step | [006_ablation_summary.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/006_ablation_summary.md) |
| **007** | Confidence Calibration | Reliability Verification | Monotonic Accuracy vs Confidence correlation | [007_confidence_calibration.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/007_confidence_calibration.md) |
| **008** | Global Key Estimation | Diatonic Prior Weighting | 100% key accuracy, CSR +2.2pp avg gain | [008_key_estimation.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/008_key_estimation.md) |
| **009** | Weighted Harmonic Templates | Template Weighting Fix | Fixed binary 1.0 bug, CSR +23.5pp on Rock | [009_weighted_templates.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/009_weighted_templates.md) |
| **010** | Chroma Feature Comparison | CQT vs STFT vs CENS | Verified CQT (68.3%) > CENS (64.8%) > STFT (6.3%) | [010_chroma_feature_comparison.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/010_chroma_feature_comparison.md) |
| **011** | Root Emphasis Grid Search | Root vs Fifth Emphasis | Optimal $w_5=0.50$, Peak CSR 69.6% (+40.0pp) | [011_root_emphasis.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/011_root_emphasis.md) |
| **012** | Distance Metrics Ablation | Cosine vs Pearson vs L2 vs L1 | Confirmed Cosine (69.6%) > L2 (64.0%) > Pearson (61.5%) | [012_distance_metrics_ablation.md](file:///c:/Users/MY%20PC/Documents/Chord%20AI/docs/experiments/012_distance_metrics_ablation.md) |

---

## Cumulative Benchmark Progress

| Benchmark Track | Baseline CSR | Post-Optimization CSR | Total CSR Gain | Baseline N-rate | Final N-rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **Rock Backing Track** | 29.6% | **69.6%** | **+40.0pp** 🚀🚀 | 25.4% | **0.0%** |
| **Chạy Ngay Đi** | 6.1% | **16.8%** | **+10.7pp** 📈 | 27.8% | **0.0%** |
| **Nếu Như Ta Chẳng Còn** | 13.4% | **14.1%** | **+0.7pp** | 19.3% | **0.0%** |
| **Average Across All Tracks** | **16.4%** | **33.5%** | **+17.1pp** | **24.2%** | **0.0%** |
