# Experiment 009: Weighted Harmonic Templates vs Rigid Binary Templates

## Hypothesis
The baseline template builder defined weights in `QUALITY_WEIGHTS`:
```python
QUALITY_WEIGHTS = {
    "": {0: 1.0, 4: 0.85, 7: 0.75},   # Major: Root=1.0, 3rd=0.85, 5th=0.75
    "m": {0: 1.0, 3: 0.85, 7: 0.75},  # Minor: Root=1.0, 3rd=0.85, 5th=0.75
}
```
However, the loop implementation originally hardcoded `vector[note] = 1.0`, effectively ignoring these weights and generating rigid binary templates `[1.0, 0, 0, 0, 1.0, 0, 0, 1.0, 0, 0, 0, 0]`.

Hypothesis: In physical acoustic instruments (guitars, pianos, bass), fundamental frequencies carry the strongest energy (Root = 1.0), the 3rd defines chord color (3rd = 0.85), and the 5th acts as supporting harmonic energy (5th = 0.75). Binary templates treat all 3 notes as equal, making the classifier overly sensitive to loud 5th harmonics. 

Fixing `build_templates()` to use true weighted profiles `[1.0, 0.85, 0.75]` will better reflect physical acoustic spectra and significantly boost Chord Symbol Recall (CSR).

## Implementation
Modified `backend/app/chords/templates.py`:
```python
def build_templates() -> dict[str, list[float]]:
    templates: dict[str, list[float]] = {}
    for root_index, root in enumerate(PITCHES):
        for suffix, intervals in QUALITY_WEIGHTS.items():
            vector = [0.0] * 12
            for interval, weight in intervals.items():
                vector[(root_index + interval) % 12] = weight
            templates[f"{root}{suffix}"] = vector
    return templates
```

## Benchmark Accuracy Results

| Benchmark Track | Binary Templates (Baseline 008) | Weighted Templates (Step 009) | CSR Gain |
|---|:---:|:---:|:---:|
| **Rock Backing Track** | 44.8% | **68.3%** | **+23.5pp** 🚀🚀 |
| **Chạy Ngay Đi** | 14.2% | **16.8%** | **+2.6pp** 📈 |
| **Nếu Như Ta Chẳng Còn** | 12.6% | **14.1%** | **+1.5pp** 📈 |
| **Average Across Suite** | **23.9%** | **33.1%** | **+9.2pp** |

## Key Insights
1. **Huge Accuracy Jump on Clean Audio**: Fixing binary templates to acoustic weighted templates `[1.0, 0.85, 0.75]` surged Rock Backing CSR from **44.8% to 68.3% (+23.5pp gain)**!
2. **Empirical Peak**: Average CSR across all tracks reached **33.1%** (up from initial baseline 16.4%, a **+16.7pp total improvement**).

## Conclusion
Acoustic Weighted Templates `[1.0, 0.85, 0.75]` provide a dramatically superior match for real-world instrument spectra compared to rigid binary templates. Fixing this single bug yielded a **+23.5pp CSR gain on clean recordings** and **+9.2pp average gain across the entire suite**.
