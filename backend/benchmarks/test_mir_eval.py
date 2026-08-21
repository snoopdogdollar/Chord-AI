"""Quick test: verify mir_eval is working correctly and investigate
why the same code produces 45.4% now vs 69.6% before."""

import mir_eval
import numpy as np
print(f"mir_eval version: {mir_eval.__version__}")

# Perfect match test
ref_intervals = np.array([[0.0, 2.0]])
ref_labels = ["G:maj"]
est_intervals = np.array([[0.0, 2.0]])
est_labels = ["G:maj"]
scores = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
print(f"Perfect match: majmin={scores.get('majmin', 'N/A')}")

# Bm predicted when G is GT
est_labels2 = ["B:min"]
scores2 = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels2)
print(f"Bm vs G: majmin={scores2.get('majmin', 'N/A')}")

# Now check: does the _to_mir_eval_label function work for A#?
from app.chords.evaluation import _to_mir_eval_label
test_labels = ["C", "Am", "G", "F", "A#", "Dm", "Bm", "N"]
print("\nLabel conversion test:")
for lbl in test_labels:
    print(f"  {lbl} -> {_to_mir_eval_label(lbl)}")

# Check: does mir_eval accept A#:maj? Or does it need Bb:maj?
ref_i = np.array([[0.0, 2.0]])
est_i = np.array([[0.0, 2.0]])
try:
    s = mir_eval.chord.evaluate(ref_i, ["A#:maj"], est_i, ["A#:maj"])
    print(f"\nA#:maj self-match: majmin={s.get('majmin', 'N/A')}")
except Exception as e:
    print(f"\nA#:maj ERROR: {e}")

try:
    s = mir_eval.chord.evaluate(ref_i, ["Bb:maj"], est_i, ["Bb:maj"])
    print(f"Bb:maj self-match: majmin={s.get('majmin', 'N/A')}")
except Exception as e:
    print(f"Bb:maj ERROR: {e}")

# Cross test: A# vs Bb
try:
    s = mir_eval.chord.evaluate(ref_i, ["A#:maj"], est_i, ["Bb:maj"])
    print(f"A#:maj vs Bb:maj: majmin={s.get('majmin', 'N/A')}")
except Exception as e:
    print(f"A# vs Bb ERROR: {e}")
