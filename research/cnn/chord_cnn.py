"""Portable GuitarSet CNN baseline. The notebook embeds and exports this module."""
import re
import numpy as np
import librosa
import torch
from torch import nn

ROOTS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
LABELS = [root + ':' + quality for quality in ('maj', 'min') for root in ROOTS]
DEFAULT_CONFIG = dict(sr=22050, hop_length=512, fmin=32.70319566257483,
                      n_bins=84, bins_per_octave=12, window_frames=43,
                      stride_frames=5, db_floor=-80.0)


def reduce_chord(label):
    """Explicit maj/min reduction; unsupported/unknown/no-chord -> ignore (-1).

    Seventh/sixth extensions below are intentionally reduced to their triad.
    Alterations, explicit pitch lists, suspended/dim/aug chords are not guessed.
    """
    match = re.fullmatch(r'([A-G])([b#]?)(?::(maj|min|7|maj7|min7|maj6|min6|9|maj9|min9|11|min11|13|min13))?(?:/[b#]*[1-7])?', label)
    if not match:
        return -1
    letter, accidental, quality = match.groups()
    root = ({'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[letter]
            + {'': 0, '#': 1, 'b': -1}[accidental]) % 12
    return root + (12 if quality and quality.startswith('min') else 0)


def group_id(track_id):
    # 00_BN1-129-Eb_comp -> BN1. Group both tempos, keys, players, comp/solo.
    fields = track_id.split('_')
    if len(fields) != 3 or not re.fullmatch(r'(BN|Jazz|Rock|SS|Funk)[1-3]', fields[1].split('-')[0]):
        raise ValueError(f'Unexpected GuitarSet track id: {track_id}')
    return fields[1].split('-')[0]


def extract_cqt(path, config):
    y, _ = librosa.load(path, sr=config['sr'], mono=True, res_type='soxr_hq')
    if len(y) < config['sr'] or not np.isfinite(y).all():
        raise ValueError(f'Audio too short or non-finite: {path}')
    magnitude = np.abs(librosa.cqt(y, sr=config['sr'], hop_length=config['hop_length'],
        fmin=config['fmin'], n_bins=config['n_bins'], bins_per_octave=config['bins_per_octave'],
        tuning=0.0, pad_mode='constant'))
    # Fixed amplitude reference (not per-song max); same rule at inference.
    db = librosa.amplitude_to_db(magnitude, ref=1.0, top_db=None)
    features = np.clip(db, config['db_floor'], 0.0)
    features = ((features - config['db_floor']) / -config['db_floor']).astype('float32')
    return features, len(y) / config['sr']


def patch_at(features, frame, width):
    assert width % 2 == 1
    half = width // 2
    indices = np.clip(np.arange(frame - half, frame + half + 1), 0, features.shape[1] - 1)
    return features[:, indices].copy()


class ChordCNN(nn.Module):
    def __init__(self, num_classes=24):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            # Keep pitch-position information; don't average the entire frequency axis.
            nn.AdaptiveAvgPool2d((12, 1)))
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(0.3), nn.Linear(64 * 12, num_classes))

    def forward(self, x):
        return self.classifier(self.features(x))


def load_model(checkpoint_path, device='cpu'):
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    if checkpoint['architecture'] != 'ChordCNN-v1':
        raise ValueError('Unsupported architecture')
    model = ChordCNN(len(checkpoint['labels'])).to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model, checkpoint


@torch.inference_mode()
def predict_audio(audio_path, checkpoint_path, device='cpu', batch_size=128):
    model, checkpoint = load_model(checkpoint_path, device)
    config = checkpoint['config']
    features, duration = extract_cqt(audio_path, config)
    step = config['hop_length'] / config['sr']
    centers = [i for i in range(0, features.shape[1], config['stride_frames']) if i * step < duration]
    outputs = []
    for offset in range(0, len(centers), batch_size):
        batch = np.stack([patch_at(features, i, config['window_frames']) for i in centers[offset:offset+batch_size]])
        outputs.extend(model(torch.from_numpy(batch[:, None]).to(device)).softmax(1).cpu().numpy())
    outputs = np.asarray(outputs)
    predictions = outputs.argmax(1)
    times = np.asarray(centers) * step
    edges = np.r_[0.0, (times[:-1] + times[1:]) / 2, duration]
    segments = []
    for i, label_id in enumerate(predictions):
        label = checkpoint['labels'][int(label_id)]
        if segments and segments[-1]['chord'] == label:
            segments[-1]['end'] = float(edges[i+1])
        else:
            segments.append(dict(start=float(edges[i]), end=float(edges[i+1]), chord=label))
    # No silence/unknown rejection or production smoothing in this baseline.
    return segments
