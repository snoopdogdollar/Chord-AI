"""Score saved raw/smoothed timelines by exact duration overlap with a reference."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re


def label(value):
    match = re.fullmatch(r'([A-G][#b]?)(?:(m)|:(maj|min))?', value)
    if not match:
        raise ValueError(f'Unsupported evaluation label: {value}')
    root, minor, quality = match.groups()
    return root + ':' + ('min' if minor else quality or 'maj')


def validate(events):
    previous_end = 0.0
    for event in events:
        start, end = event['start'], event['end']
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end
                and start >= previous_end - 1e-8):
            raise ValueError(f'Invalid interval: {event}')
        label(event['chord'])
        previous_end = end


def score(reference, predictions, start, end):
    total = matched = 0.0
    by_chord = {}
    for ref in reference:
        left, right = max(start, ref['start']), min(end, ref['end'])
        if right <= left:
            continue
        chord = label(ref['chord'])
        seconds = right - left
        total += seconds
        bucket = by_chord.setdefault(chord, {'reference_seconds': 0.0, 'correct_seconds': 0.0})
        bucket['reference_seconds'] += seconds
        for pred in predictions:
            if label(pred['chord']) == chord:
                overlap = max(0.0, min(right, pred['end']) - max(left, pred['start']))
                matched += overlap
                bucket['correct_seconds'] += overlap
    if total <= 0:
        raise ValueError('No reference coverage in requested interval')
    return {'reference_seconds': total, 'correct_seconds': matched,
            'duration_accuracy': matched / total, 'by_chord': by_chord}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True, type=Path)
    parser.add_argument('--comparison-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--reference-status', default='Repository benchmark; manual verification not established')
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text(encoding='utf-8'))['annotations']
    comparison = json.loads((args.comparison_dir / 'comparison.json').read_text())
    duration = comparison['duration_seconds']
    validate(reference)
    report = {'reference': str(args.reference.resolve()),
              'reference_sha256': hashlib.sha256(args.reference.read_bytes()).hexdigest(),
              'reference_status': args.reference_status,
              'comparison_dir': str(args.comparison_dir.resolve()),
              'checkpoint_sha256': comparison.get('checkpoint_sha256'),
              'audio': comparison['audio'], 'audio_duration': duration,
              'smoothing_seconds': comparison['smoothing_seconds'],
              'metric': 'Exact maj/min label overlap / annotated duration; unannotated time excluded; no offset adjustment',
              'annotated_start': reference[0]['start'], 'annotated_end': min(reference[-1]['end'], duration)}
    for name in ('raw', 'smoothed'):
        predictions = json.loads((args.comparison_dir / f'{name}.json').read_text())
        validate(predictions)
        report[name] = score(reference, predictions, 0, duration)
        report[name]['focus_33_39'] = score(reference, predictions, 33, 39)
    report['delta_percentage_points'] = 100 * (report['smoothed']['duration_accuracy'] - report['raw']['duration_accuracy'])
    report['delta_correct_seconds'] = report['smoothed']['correct_seconds'] - report['raw']['correct_seconds']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
