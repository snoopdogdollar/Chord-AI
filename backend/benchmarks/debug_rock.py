"""Debug script: investigate Rock Backing CSR regression."""
import json
import soundfile as sf
from pathlib import Path
from app.audio.features import extract_chroma_features
from app.audio.beats import detect_beats
from app.chords.detector import ChordDetector, mean_vector
from app.chords.evaluation import evaluate, load_annotations
from app.chords.key_estimation import estimate_key, get_diatonic_chords
from app.core.config import Settings

settings = Settings()

wav = Path("data/processed/fast_rock_backing_c_major/normalized.wav")
ann = Path("benchmarks/annotations/rock_backing_c_major.json")

y, sr = sf.read(str(wav))
dur = float(len(y) / sr)

features = extract_chroma_features(wav, settings)
beats = detect_beats(wav, settings)
events = ChordDetector().detect(features, beats)
annotations = load_annotations(ann)
result = evaluate(events, annotations, dur)

print(f"Rock Backing CSR majmin = {result.csr_majmin*100:.1f}%")
print(f"Rock Backing CSR root   = {result.csr_root*100:.1f}%")

print(f"\nTotal predicted events: {len(events)}")
print(f"Total GT annotations:  {len(annotations)}")
print(f"Detected BPM: {beats.bpm}")

global_chroma = mean_vector(features.chroma)
key_root, key_mode = estimate_key(global_chroma)
diatonic = get_diatonic_chords(key_root, key_mode)
print(f"Detected Key: {key_root} {key_mode}")
print(f"Diatonic chords: {sorted(diatonic)}")

print("\nFirst 20 predicted events:")
for e in events[:20]:
    print(f"  {e.start:7.2f}s - {e.end:7.2f}s : {e.chord}")

print("\nFirst 10 GT annotations:")
for a in annotations[:10]:
    print(f"  {a.start:7.2f}s - {a.end:7.2f}s : {a.chord}")

# Check what the detector predicts for the G chord region
print("\n--- G chord regions in GT ---")
for a in annotations:
    if a.chord == "G":
        # Find what was predicted in this region
        preds_in_region = [e for e in events if e.start < a.end and e.end > a.start]
        for p in preds_in_region:
            print(f"  GT: G ({a.start:.2f}-{a.end:.2f}) | Pred: {p.chord} ({p.start:.2f}-{p.end:.2f})")
        if not preds_in_region:
            print(f"  GT: G ({a.start:.2f}-{a.end:.2f}) | Pred: NONE")
        break  # Just show first G region for debugging
