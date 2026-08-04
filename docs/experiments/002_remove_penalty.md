# Experiment 002: Removal of Non-Chord Penalty

## Hypothesis
The original classifier included a `non_chord_penalty` function:
```python
def non_chord_penalty(chroma_vector: list[float], template: list[float]) -> float:
    outside_values = [chroma for chroma, template_value in zip(chroma_vector, template) if template_value == 0.0]
    return sum(outside_values) / len(outside_values) * 0.18
```
This logic subtracted score if chroma energy was detected on pitch classes outside the target chord template.
Hypothesis: In real-world acoustic recordings, musical instruments produce natural harmonic overtones (e.g., 3rd and 5th harmonics) and room acoustics introduce low-level energy across non-triad pitch classes. Penalizing non-template energy lowers cosine similarity for correctly played chords, causing valid chords to fall below classification thresholds. Removing this penalty will stabilize chord matching.

## Implementation
1. Modified `backend/app/chords/classifier.py`:
   - Removed `non_chord_penalty` calculation and function definition.
   - Simplified `classify_chroma` loop to rely strictly on Cosine Similarity:
     ```python
     for label, template in CHORD_TEMPLATES.items():
         score = cosine_similarity(chroma, template)
         scored.append((label, score))
     ```

## Benchmark
Ran parameter grid search testing penalty weights `0.0`, `0.05`, and `0.18` across all benchmark tracks.

## Result
- `penalty_weight = 0.0`: Highest average CSR across all tracks.
- `penalty_weight = 0.18` (original): Reduced CSR by penalizing natural instrument overtones.
- Combined with template reduction, removing the penalty improved template match stability for triads with rich harmonics (e.g., guitar and piano chords).

## Conclusion
Hard penalties on non-template chroma energy harm chord recognition accuracy in real audio because acoustic instruments inherently generate non-triad harmonic overtones. Pure Cosine Similarity without negative energy penalties yields superior classification robustness.
