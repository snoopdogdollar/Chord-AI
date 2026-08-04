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

---

## Cumulative Benchmark Progress

| Benchmark Track | Baseline CSR | Final Optimized CSR | Total CSR Gain | Baseline N-rate | Final N-rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **Rock Backing Track** | 29.6% | **41.7%** | **+12.1pp** | 25.4% | **0.0%** |
| **Chạy Ngay Đi** | 6.1% | **12.3%** | **+6.2pp** | 27.8% | **0.0%** |
| **Nếu Như Ta Chẳng Còn** | 13.4% | **11.2%** | -2.2pp | 19.3% | **0.0%** |
| **Average Across All Tracks** | **16.4%** | **21.7%** | **+5.3pp** | **24.2%** | **0.0%** |
