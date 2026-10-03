"""Save raw and smoothed CNN timelines from a single inference pass."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch
from chord_cnn import predict_probabilities
from cnn_smoothing import decode_segments, smooth_probabilities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', required=True, type=Path)
    parser.add_argument('--checkpoint', type=Path, default=Path(__file__).resolve().parent / 'data/trained_bundle_20260928/best.pth')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seconds', type=float, default=0.4)
    parser.add_argument('--focus-start', type=float, default=33.0)
    parser.add_argument('--focus-end', type=float, default=39.0)
    args = parser.parse_args()
    if not args.audio.is_file() or not args.checkpoint.is_file():
        parser.error('Audio or checkpoint does not exist')
    if not np.isfinite(args.seconds) or args.seconds < 0:
        parser.error('--seconds must be finite and nonnegative')
    if not 0 <= args.focus_start < args.focus_end:
        parser.error('Invalid focus interval')
    # Avoid accidentally overwriting a previous experiment.
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    started = time.perf_counter()
    times, raw, duration, labels = predict_probabilities(args.audio, args.checkpoint, batch_size=64)
    smoothed = smooth_probabilities(times, raw, args.seconds)
    timelines = {name: decode_segments(times, probabilities, duration, labels)
                 for name, probabilities in [('raw', raw), ('smoothed', smoothed)]}
    for name, timeline in timelines.items():
        (args.output / f'{name}.json').write_text(json.dumps(timeline, indent=2), encoding='utf-8')
    np.savez_compressed(args.output / 'probabilities.npz', times=times, raw=raw,
                        smoothed=smoothed, labels=np.asarray(labels), duration=duration)
    with (args.output / 'focus_probabilities.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'raw_label', 'smoothed_label'] + [f'raw_{x}' for x in labels] + [f'smoothed_{x}' for x in labels])
        for i in np.flatnonzero((times >= args.focus_start) & (times <= args.focus_end)):
            writer.writerow([float(times[i]), labels[int(raw[i].argmax())], labels[int(smoothed[i].argmax())], *raw[i].tolist(), *smoothed[i].tolist()])
    report = dict(audio=str(args.audio), checkpoint=str(args.checkpoint),
                  checkpoint_sha256=hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
                  duration_seconds=duration, smoothing_seconds=args.seconds,
                  method='centered mean of probabilities; no label overrides',
                  elapsed_seconds=time.perf_counter() - started,
                  focus=[args.focus_start, args.focus_end],
                  changed_frames=int(np.sum(raw.argmax(1) != smoothed.argmax(1))),
                  note='Fewer transitions is not proof of higher accuracy. No independently verified boundaries supplied.')
    for name, timeline in timelines.items():
        report[name] = dict(segment_count=len(timeline),
                            segments_under_0_3_seconds=sum(e['end'] - e['start'] < 0.3 for e in timeline),
                            focus_segments=[e for e in timeline if e['end'] > args.focus_start and e['start'] < args.focus_end])
    (args.output / 'comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
