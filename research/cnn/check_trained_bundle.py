"""Bounded CPU smoke test on 10-40 seconds of the existing rock benchmark."""
import json
import argparse
from pathlib import Path
import time

import soundfile as sf
import torch
from chord_cnn import load_model, predict_audio

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / 'research/cnn/data/trained_bundle_20260928'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=BUNDLE / 'cpu_check')
args = parser.parse_args()
OUTPUT = args.output
OUTPUT.mkdir(parents=True, exist_ok=True)
torch.set_num_threads(2)
model, checkpoint = load_model(BUNDLE / 'best.pth', 'cpu')
assert checkpoint['labels'] == json.loads((BUNDLE / 'labels.json').read_text())
assert checkpoint['config'] == json.loads((BUNDLE / 'config.json').read_text())
assert checkpoint['epoch'] == 9 and not checkpoint['smoke_test']
with torch.inference_mode():
    logits = model(torch.zeros(1, 1, 84, 43))
    assert logits.shape == (1, 24) and torch.isfinite(logits).all()
print('Checkpoint CPU load and forward: passed', flush=True)
audio = ROOT / 'backend/data/processed/fast_rock_backing_c_major/normalized.wav'
start, end = 10.0, 40.0
with sf.SoundFile(audio) as stream:
    stream.seek(int(start * stream.samplerate))
    clip = stream.read(int((end - start) * stream.samplerate))
    sf.write(OUTPUT / 'rock_10_40.wav', clip, stream.samplerate, subtype='FLOAT')
t0 = time.perf_counter()
predictions = predict_audio(OUTPUT / 'rock_10_40.wav', BUNDLE / 'best.pth', batch_size=64)
elapsed = time.perf_counter() - t0
for event in predictions:
    event['start'] += start
    event['end'] += start
assert abs(predictions[0]['start'] - start) < 1e-6
assert abs(predictions[-1]['end'] - end) < 1e-3

def canonical(chord):
    if ':' in chord or chord == 'N':
        return chord
    return chord[:-1] + ':min' if chord.endswith('m') else chord + ':maj'

reference = json.loads((ROOT / 'backend/benchmarks/annotations/rock_backing_c_major.json').read_text())
correct = total = 0.0
for ref in reference['annotations']:
    left, right = max(start, ref['start']), min(end, ref['end'])
    if right <= left:
        continue
    total += right - left
    for pred in predictions:
        if canonical(ref['chord']) == pred['chord']:
            correct += max(0, min(right, pred['end']) - max(left, pred['start']))
report = dict(checkpoint_load='passed', device='cpu', threads=2,
              source_audio=str(audio), start=start, end=end, cold_inference_seconds=elapsed,
              annotated_seconds=total, matching_seconds=correct,
              exact_label_duration_accuracy=correct / total if total else None,
              reference_notes=reference.get('notes'), reference_source=reference.get('source'),
              limitation='One short crop; reference is generated from presumed progression/timing. Not independently hand-verified. No current DSP comparison.',
              predictions=predictions)
(OUTPUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'predictions'}, indent=2))
