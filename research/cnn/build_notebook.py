"""Build a standalone Kaggle notebook; does not train or download data locally."""
import ast
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
cells = []


def md(text):
    cells.append(dict(cell_type='markdown', metadata={}, source=text.strip().splitlines(True)))


def code(text):
    text = text.strip() + '\n'
    ast.parse(text)
    cells.append(dict(cell_type='code', execution_count=None, metadata={}, outputs=[], source=text.splitlines(True)))


md('''# Train CNN nhận diện hợp âm trên Kaggle — GuitarSet

**Toàn bộ tải dữ liệu, tạo đặc trưng và train chạy trên Kaggle. Laptop chỉ nhận bundle để inference.**

| Image classification | Notebook này |
|---|---|
| Ảnh RGB `[3,H,W]` | CQT `[1,84,43]`: cao độ × thời gian |
| Nhãn của ảnh | Nhãn hợp âm tại tâm cửa sổ audio khoảng 1 giây |
| Dataset / DataLoader | Cắt cửa sổ từ CQT đã tính một lần cho mỗi bản ghi |
| CrossEntropyLoss, backprop | Giống image classification |
| `model.pth` | `best.pth` + code + cấu hình + nhãn + báo cáo |

Đây là baseline học **24 lớp: 12 trưởng + 12 thứ**. Hợp âm 7/6/9... được quy về
triad theo bảng trong code. `N`, `X`, sus/dim/aug và dạng không hỗ trợ bị **bỏ khỏi
loss/metric**, không giả thành hợp âm trưởng/thứ. Model chưa có khả năng phát hiện
im lặng/no-chord: khi inference luôn chọn một trong 24 lớp.

GuitarSet là guitar, không đại diện cho bài hát phối nhiều nhạc cụ.
Notebook không sửa backend Chord AI và không khẳng định tốt hơn DSP trước khi đo.

## Cách chạy
1. Tạo notebook Kaggle, import file `.ipynb` này.
2. Chọn accelerator **GPU** trong cài đặt notebook. Chỉ sử dụng một GPU.
3. Bật Internet nếu muốn notebook tải trực tiếp hai zip từ Zenodo (~696 MB).
   Hoặc thêm Kaggle Dataset chứa `annotation.zip` và `audio_mono-mic.zip` vào Input.
   Dataset đã giải nén, có `.jams` và `*_mic.wav`, cũng được hỗ trợ.
4. Chạy lần lượt các cell; nghe/xem mẫu ở bước 5 trước khi chạy training.
5. Sau khi hoàn tất, lưu phiên bản có output và tải `chord_cnn_bundle.zip`.

Nguồn: [GuitarSet](https://guitarset.weebly.com/),
[GuitarSet 1.1.0 / Zenodo](https://zenodo.org/records/3371780),
[mirdata: thứ tự annotation](https://mirdata.readthedocs.io/en/stable/_modules/mirdata/datasets/guitarset.html),
[PyTorch checkpoint](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html),
[librosa CQT](https://librosa.org/doc/0.11.0/generated/librosa.cqt.html).
''')
md('''## 1. Môi trường và cấu hình
Cell đầu dừng nếu không ở Kaggle hoặc GPU chưa bật, tránh chạy nhầm trên laptop.
Giữ PyTorch do Kaggle cung cấp để không làm hỏng CUDA. Chỉ cài thư viện còn thiếu.
`SMOKE_TEST=True` chạy 2 epoch để kiểm tra luồng, **không phải kết quả cuối**.
Sau smoke test, đổi thành False và chạy lại từ đầu để train đầy đủ.''')
code('''from pathlib import Path
import os, sys, subprocess, importlib.util
assert Path('/kaggle/working').is_dir(), 'Hãy import và chạy notebook này trên Kaggle.'
assert importlib.util.find_spec('torch'), 'Chọn Kaggle Python GPU image có PyTorch.'
import torch
assert torch.cuda.is_available(), 'Bật GPU trong Settings rồi khởi động lại session.'
packages = {'librosa': 'librosa==0.11.0', 'soundfile': 'soundfile>=0.12',
            'sklearn': 'scikit-learn>=1.3', 'matplotlib': 'matplotlib', 'pandas': 'pandas', 'tqdm': 'tqdm'}
missing = [package for module, package in packages.items() if importlib.util.find_spec(module) is None]
if missing:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
import json, random, hashlib, zipfile, shutil, urllib.request, warnings, time
from collections import Counter
import numpy as np
import pandas as pd
import librosa, soundfile as sf
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
from IPython.display import Audio, display, FileLink
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from torch.utils.data import Dataset, DataLoader

SEED = 42
SMOKE_TEST = False
ALLOW_DOWNLOAD = True  # Chỉ tải trên Kaggle; False nếu đã gắn Input đầy đủ.
INPUT = Path('/kaggle/input')  # Có thể trỏ tới đúng thư mục dataset nếu gắn nhiều nguồn.
WORK = Path('/kaggle/working/chord_cnn')
WORK.mkdir(exist_ok=True)
RUN = WORK / ('smoke' if SMOKE_TEST else 'full')
RUN.mkdir(exist_ok=True)
BUNDLE = RUN / 'bundle'
BUNDLE.mkdir(exist_ok=True)
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.benchmark = False
torch.backends.cudnn.deterministic = True
DEVICE = 'cuda'
print('GPU:', torch.cuda.get_device_name(0), '| PyTorch:', torch.__version__, '| librosa:', librosa.__version__)
''')
md('''## 2. Code dùng chung cho train và inference
Cell này ghi `chord_cnn.py` vào output. Khi tải về máy, dùng chính file này để
đảm bảo cùng kiến trúc CNN, CQT và cách chuẩn hóa. Không cần biến CQT thành PNG:
CNN nhận trực tiếp ma trận số, không có trục/chữ/màu của biểu đồ.''')
module_source = (HERE / 'chord_cnn.py').read_text(encoding='utf-8')
code('MODULE_SOURCE = ' + repr(module_source) + '\nSMOOTHING_SOURCE = ' + repr((HERE / 'cnn_smoothing.py').read_text(encoding='utf-8')) + '''
(BUNDLE / 'cnn_smoothing.py').write_text(SMOOTHING_SOURCE, encoding='utf-8')
sys.path.insert(0, str(BUNDLE))
(BUNDLE / 'chord_cnn.py').write_text(MODULE_SOURCE, encoding='utf-8')
import importlib.util
spec = importlib.util.spec_from_file_location('chord_cnn', BUNDLE / 'chord_cnn.py')
cnn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cnn)
CONFIG = dict(cnn.DEFAULT_CONFIG)
LABELS = cnn.LABELS
print(dict(enumerate(LABELS)))
''')
md('''## 3. Lấy dữ liệu trên Kaggle và kiểm tra cặp audio/nhãn
Nếu Input có dữ liệu giải nén, notebook dùng trực tiếp. Nếu có zip, kiểm tra MD5
trước khi giải nén. Nếu thiếu, tải bản chính thức về `/kaggle/working`.
Nếu Zenodo trả 429/403 hoặc Internet bị tắt, thêm hai zip vào Input rồi chạy lại;
không cần tải audio về laptop để train.

Chọn annotation **performed/inferred** (phần tử chord thứ hai theo mirdata).
Nhãn này được suy ra từ nốt chơi, không phải nhãn nghe thủ công hoàn hảo.
Loại cả cặp comp/solo của hai bản thu có [lỗi timing đã biết](https://github.com/marl/GuitarSet/issues/5).''')
code('''ARCHIVES = {'annotation.zip': 'b39b78e63d3446f2e54ddb7a54df9b10',
            'audio_mono-mic.zip': '275966d6610ac34999b58426beb119c3'}
DATA = WORK / 'data'
DATA.mkdir(exist_ok=True)

def md5_file(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def unpack_archive(name, digest):
    candidates = sorted(INPUT.rglob(name))
    if len(candidates) > 1:
        raise ValueError(f'Nhiều {name}: đặt INPUT tới một dataset cụ thể.')
    archive = candidates[0] if candidates else DATA / name
    if not archive.exists():
        if not ALLOW_DOWNLOAD:
            raise FileNotFoundError(f'Thiếu {name}; thêm vào Input hoặc bật ALLOW_DOWNLOAD.')
        url = f'https://zenodo.org/records/3371780/files/{name}?download=1'
        part = archive.with_suffix('.zip.part')
        print('Downloading', name, flush=True)
        with urllib.request.urlopen(url, timeout=90) as response, part.open('wb') as output:
            total = int(response.headers.get('Content-Length', 0))
            with tqdm(total=total or None, unit='B', unit_scale=True) as progress:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    output.write(block); progress.update(len(block))
        assert md5_file(part) == digest, f'Checksum sai: {name}'
        part.replace(archive)
    assert md5_file(archive) == digest, f'Checksum sai: {archive}. Lấy lại bản chính thức.'
    destination = DATA / name.removesuffix('.zip')
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            target = (destination / item.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError('Unsafe archive path')
        z.extractall(destination)
    return destination

def unique_index(paths, suffix):
    result = {}
    for p in paths:
        if '__MACOSX' in p.parts or p.name.startswith('._'):
            continue
        key = p.stem.removesuffix(suffix)
        if key in result:
            raise ValueError(f'Trùng track {key}: đặt INPUT tới một nguồn duy nhất.')
        result[key] = p
    return result

jams_paths = list(INPUT.rglob('*.jams'))
wav_paths = list(INPUT.rglob('*_mic.wav'))
# Kaggle may expose the sanitized upload as a ZIP instead of extracting it.
safe_archives = list(INPUT.rglob('guitarset_kaggle.zip'))
if not jams_paths and not wav_paths and safe_archives:
    assert len(safe_archives) == 1, 'Chỉ gắn một guitarset_kaggle.zip.'
    destination = DATA / 'kaggle_safe'
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(safe_archives[0]) as z:
        for item in z.infolist():
            assert (destination / item.filename).resolve().is_relative_to(destination.resolve()), 'Unsafe ZIP path'
        assert z.testzip() is None, 'ZIP bị hỏng.'
        z.extractall(destination)
    jams_paths = list(destination.rglob('*.jams'))
    wav_paths = list(destination.rglob('*_mic.wav'))
if not jams_paths:
    jams_paths = list(unpack_archive('annotation.zip', ARCHIVES['annotation.zip']).rglob('*.jams'))
if not wav_paths:
    wav_paths = list(unpack_archive('audio_mono-mic.zip', ARCHIVES['audio_mono-mic.zip']).rglob('*_mic.wav'))
jams_index = unique_index(jams_paths, '')
wav_index = unique_index(wav_paths, '_mic')
assert set(jams_index) == set(wav_index), 'Audio và JAMS không khớp track id.'
assert len(jams_index) == 360, f'Cần bản GuitarSet đầy đủ: đang có {len(jams_index)} cặp.'
BAD_PAIRS = {'04_BN3-154-E', '04_Jazz1-200-B'}
records, excluded = [], []
for track in sorted(jams_index):
    if track.rsplit('_', 1)[0] in BAD_PAIRS:
        excluded.append(track); continue
    info = sf.info(wav_index[track])
    doc = json.loads(jams_index[track].read_text())
    variants = [a for a in doc['annotations'] if a['namespace'] == 'chord']
    assert len(variants) == 2, track
    events = variants[1]['data']
    assert events, track
    previous_end = 0.0
    for event in events:
        start, length = float(event['time']), float(event['duration'])
        assert np.isfinite([start, length]).all() and start >= 0 and length > 0, track
        assert start >= previous_end - 1e-5 and start + length <= info.duration + 0.1, track
        previous_end = start + length
    records.append(dict(track=track, audio=str(wav_index[track]), events=events,
                        duration=info.duration, group=cnn.group_id(track)))
print('Dùng:', len(records), '| Loại do timing:', excluded)
display(pd.DataFrame([{k: r[k] for k in ('track', 'duration', 'group')} for r in records]).head())
print('Metadata kiểu annotation đã chọn:', variants[1].get('annotation_metadata'))
''')
md('''## 4. Chia nhóm trước khi cắt cửa sổ
Không dùng `random_split` trên các cửa sổ: chúng chồng lấn và dễ làm rò rỉ dữ liệu.
Nhóm `BN1`, `Jazz2`... giữ chung người chơi, key, tempo và comp/solo của cùng
style/progression. Có 15 nhóm; chia cố định 9 train / 3 validation / 3 test.
Đây vẫn chưa phải đánh giá trên những progression hoàn toàn mới, vì các style
chia sẻ một số cấu trúc hòa âm. Không đổi seed để săn điểm test cao.

Test chỉ dùng ở cuối. Validation dùng chọn epoch tốt nhất.''')
code('''groups = sorted({r['group'] for r in records})
assert len(groups) == 15, groups
random.Random(SEED).shuffle(groups)
split_groups = {'train': groups[:9], 'val': groups[9:12], 'test': groups[12:]}
for r in records:
    r['split'] = next(name for name, ids in split_groups.items() if r['group'] in ids)
assert not set(split_groups['train']) & set(split_groups['test'])
assert not set(split_groups['val']) & set(split_groups['test'])
assert not set(split_groups['train']) & set(split_groups['val'])
split_manifest = {'seed': SEED, 'groups': split_groups, 'excluded': excluded,
                  'tracks': {r['track']: r['split'] for r in records}}
(BUNDLE / 'split_manifest.json').write_text(json.dumps(split_manifest, indent=2))
print(split_groups)
print(Counter(r['split'] for r in records))
''')
md('''## 5. Nghe và nhìn một mẫu train
CQT giống ảnh xám: trục dọc là các bin cao độ, trục ngang là thời gian.
`hop_length=512` tại 22050 Hz tương đương khoảng 23 ms/frame.
43 frame cho ngữ cảnh khoảng 1 giây; nhãn là hợp âm ở **tâm** cửa sổ.
Khác ảnh thông thường, không lật/rotate CQT: đổi trục cao độ sẽ đổi ý nghĩa nhãn.''')
code('''example = next(r for r in records if r['split'] == 'train')
features, duration = cnn.extract_cqt(example['audio'], CONFIG)
display(Audio(filename=example['audio']))
display(pd.DataFrame(example['events']).head(12))
plt.figure(figsize=(12, 4))
plt.imshow(features, origin='lower', aspect='auto', extent=[0, duration, 0, CONFIG['n_bins']], cmap='magma')
plt.xlabel('Thời gian (giây)'); plt.ylabel('CQT bin (C1 trở lên)'); plt.title(example['track'])
plt.colorbar(label='Biên độ log chuẩn hóa'); plt.show()
''')
md('''## 6. Tạo CQT và Dataset
Trích CQT dùng **CPU của Kaggle**, train CNN dùng GPU. Tính một lần cho mỗi bản
ghi, lưu cache; không tạo hàng nghìn ảnh PNG và không nhân bản toàn bộ cửa sổ trong RAM.
Cache gắn với cấu hình và phiên bản librosa, kèm fingerprint của audio.
Khoảng không có annotation và nhãn không hỗ trợ được đánh dấu -1, không coi là `N`.
Mọi split dùng cùng stride khoảng 116 ms; metric là accuracy tại tâm cửa sổ có nhãn hợp lệ,
không phải CSR liên tục trên toàn bộ audio.''')
code('''cache_key = hashlib.sha256(json.dumps({'config': CONFIG, 'librosa': librosa.__version__}, sort_keys=True).encode()).hexdigest()[:12]
CACHE = WORK / ('cache_' + cache_key)
CACHE.mkdir(exist_ok=True)
feature_bank, samples = {}, {'train': [], 'val': [], 'test': []}
coverage = {s: Counter() for s in samples}
ignored_labels = Counter()
for r in tqdm(records, desc='CQT / labels'):
    audio_digest = md5_file(Path(r['audio']))
    cache = CACHE / (r['track'] + '_' + audio_digest + '.npy')
    if cache.exists():
        matrix = np.load(cache, allow_pickle=False)
    else:
        matrix, _ = cnn.extract_cqt(r['audio'], CONFIG)
        np.save(cache, matrix)
    assert matrix.shape[0] == CONFIG['n_bins'] and np.isfinite(matrix).all()
    feature_bank[r['track']] = matrix
    times = np.arange(matrix.shape[1]) * CONFIG['hop_length'] / CONFIG['sr']
    targets = np.full(len(times), -1, dtype=np.int64)
    for event in r['events']:
        target = cnn.reduce_chord(event['value'])
        if target < 0:
            ignored_labels[event['value']] += 1
        mask = (times >= event['time']) & (times < event['time'] + event['duration'])
        targets[mask] = target
    for center in range(0, len(times), CONFIG['stride_frames']):
        if times[center] >= r['duration']:
            continue
        coverage[r['split']]['total'] += 1
        if targets[center] >= 0:
            samples[r['split']].append((r['track'], center, int(targets[center])))
            coverage[r['split']]['valid'] += 1

for s, items in samples.items():
    assert items, f'Split rỗng: {s}'
    print(s, len(items), 'cửa sổ; coverage:', coverage[s]['valid'] / coverage[s]['total'])
print('Nhãn bỏ qua (số event):', ignored_labels)
counts = {s: np.bincount([x[2] for x in items], minlength=len(LABELS)) for s, items in samples.items()}
display(pd.DataFrame(counts, index=LABELS))
missing_train = [LABELS[i] for i, n in enumerate(counts['train']) if n == 0]
if missing_train:
    warnings.warn(f'Không có mẫu train cho {missing_train}. Model không được học các lớp này; báo cáo test vẫn tính chúng.')

class ChordDataset(Dataset):
    def __init__(self, items):
        self.items = items
    def __len__(self):
        return len(self.items)
    def __getitem__(self, index):
        track, center, target = self.items[index]
        patch = cnn.patch_at(feature_bank[track], center, CONFIG['window_frames'])
        return torch.from_numpy(patch[None]), target

generator = torch.Generator().manual_seed(SEED)
loaders = {s: DataLoader(ChordDataset(items), batch_size=128, shuffle=(s == 'train'),
                        num_workers=0, pin_memory=True, generator=generator if s == 'train' else None)
           for s, items in samples.items()}
x, y = next(iter(loaders['train']))
print('Batch:', x.shape, y.shape, '| tương tự [B, channels, height, width] của ảnh')
plt.imshow(x[0, 0], origin='lower', aspect='auto', cmap='magma'); plt.title(LABELS[y[0].item()]); plt.show()
''')
md('''## 7. Train CNN
Giống image classification: logits → CrossEntropyLoss → backward → optimizer.step.
Loss không cân bằng lớp ở baseline đầu tiên; xem macro-F1 và từng lớp để tránh
accuracy bị lớp phổ biến chi phối. Best checkpoint chọn bằng **validation loss**.
Early stopping dừng sau 6 epoch không cải thiện. Không chạy test trong vòng train.
Nếu hết VRAM, giảm batch size từ 128 xuống 64 ở cell trước và chạy lại các cell sau.''')
code('''model = cnn.ChordCNN(len(LABELS)).to(DEVICE)
criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
EPOCHS = 2 if SMOKE_TEST else 35
PATIENCE = 6
history, best_loss, stale = [], float('inf'), 0
versions = {name: str(module.__version__) for name, module in
            [('torch', torch), ('numpy', np), ('librosa', librosa), ('soundfile', sf)]}

def epoch_pass(loader, training):
    model.train(training)
    loss_sum = correct = total = 0
    with torch.set_grad_enabled(training):
        for x, y in loader:
            x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
            if training:
                optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            if training:
                loss.backward()
                optimizer.step()
            loss_sum += loss.item() * len(y)
            correct += (logits.argmax(1) == y).sum().item()
            total += len(y)
    return loss_sum / total, correct / total

print('Parameters:', sum(p.numel() for p in model.parameters()))
for epoch in range(1, EPOCHS + 1):
    started = time.time()
    train_loss, train_acc = epoch_pass(loaders['train'], True)
    val_loss, val_acc = epoch_pass(loaders['val'], False)
    assert np.isfinite([train_loss, val_loss]).all(), 'Loss không hữu hạn; dừng để kiểm tra dữ liệu.'
    row = dict(epoch=epoch, train_loss=train_loss, val_loss=val_loss,
               train_acc=train_acc, val_acc=val_acc, seconds=time.time()-started)
    history.append(row); print(row)
    (BUNDLE / 'history.json').write_text(json.dumps(history, indent=2))
    if val_loss < best_loss:
        best_loss, stale = val_loss, 0
        torch.save({'architecture': 'ChordCNN-v1',
                    'model_state_dict': {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
                    'labels': LABELS, 'config': CONFIG, 'epoch': epoch, 'val_loss': val_loss,
                    'seed': SEED, 'smoke_test': SMOKE_TEST, 'versions': versions,
                    'annotation': 'GuitarSet inferred/performed (second chord annotation)',
                    'missing_train_classes': missing_train}, BUNDLE / 'best.pth')
    else:
        stale += 1
    if stale >= PATIENCE:
        print('Early stopping'); break

frame = pd.DataFrame(history)
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
frame.plot(x='epoch', y=['train_loss', 'val_loss'], ax=axes[0])
frame.plot(x='epoch', y=['train_acc', 'val_acc'], ax=axes[1])
fig.tight_layout(); fig.savefig(BUNDLE / 'learning_curves.png'); plt.show()
''')
md('''## 8. Đánh giá checkpoint tốt nhất trên test
Báo cáo accuracy, macro-F1, root accuracy, confusion matrix và từng bản ghi.
Coverage cho biết tỷ lệ tâm cửa sổ được chấm. Nhãn bỏ qua không đóng góp metric;
vì vậy không so trực tiếp số này với CSR toàn bài của detector hiện tại.
So sánh thêm baseline luôn đoán lớp phổ biến nhất trong train.
Sau khi xem test, nếu sửa model thì tập này đã trở thành dữ liệu phát triển;
cần test độc lập mới để đưa ra kết luận cuối.''')
code('''model, checkpoint = cnn.load_model(BUNDLE / 'best.pth', DEVICE)
truth, predicted = [], []
with torch.inference_mode():
    for x, y in loaders['test']:
        predicted.extend(model(x.to(DEVICE)).argmax(1).cpu().tolist())
        truth.extend(y.tolist())
truth, predicted = np.asarray(truth), np.asarray(predicted)
report = classification_report(truth, predicted, labels=list(range(len(LABELS))),
                               target_names=LABELS, output_dict=True, zero_division=0)
metrics = {'test_window_accuracy': float(np.mean(truth == predicted)),
           'test_root_accuracy': float(np.mean(truth % 12 == predicted % 12)),
           'majority_baseline_accuracy': float(np.mean(truth == counts['train'].argmax())),
           'macro_f1_all_24_classes': report['macro avg']['f1-score'],
           'coverage': {s: dict(v) for s, v in coverage.items()},
           'ignored_labels': dict(ignored_labels), 'classification_report': report,
           'missing_train_classes': missing_train, 'best_epoch': checkpoint['epoch'],
           'smoke_test': SMOKE_TEST}
(BUNDLE / 'metrics.json').write_text(json.dumps(metrics, indent=2))
print({k: v for k, v in metrics.items() if k not in ('classification_report', 'ignored_labels')})
display(pd.DataFrame(report).T)
cm = confusion_matrix(truth, predicted, labels=list(range(len(LABELS))))
fig, ax = plt.subplots(figsize=(13, 13))
ConfusionMatrixDisplay(cm, display_labels=LABELS).plot(ax=ax, xticks_rotation=90, colorbar=False)
fig.tight_layout(); fig.savefig(BUNDLE / 'confusion_matrix.png'); plt.show()
per_track = pd.DataFrame({'track': [s[0] for s in samples['test']], 'correct': truth == predicted})
per_track = per_track.groupby('track')['correct'].agg(['mean', 'count'])
per_track.to_csv(BUNDLE / 'per_track.csv'); display(per_track)
''')
md('''## 9. Thử reload và xuất bundle
Kiểm tra checkpoint nạp trên CPU cho logits gần bằng model GPU. Đây là kiểm tra
lưu/nạp, không train trên CPU. Inference demo xử lý cả một bản test và gộp các
nhãn liên tiếp giống nhau; chưa có smoothing sản phẩm hay nhận diện no-chord.
`best.pth` là checkpoint inference, không lưu optimizer để resume training.''')
code('''cpu_model, _ = cnn.load_model(BUNDLE / 'best.pth', 'cpu')
batch, _ = next(iter(loaders['test']))
with torch.inference_mode():
    torch.testing.assert_close(cpu_model(batch[:4]), model(batch[:4].to(DEVICE)).cpu(), rtol=1e-3, atol=1e-4)
print('Checkpoint reload CPU/GPU: passed')
test_example = next(r for r in records if r['split'] == 'test')
segments = cnn.predict_audio(test_example['audio'], BUNDLE / 'best.pth', device=DEVICE)
(BUNDLE / 'example_prediction.json').write_text(json.dumps({'track': test_example['track'], 'segments': segments}, indent=2))
display(pd.DataFrame(segments).head(20))
(BUNDLE / 'config.json').write_text(json.dumps(CONFIG, indent=2))
(BUNDLE / 'labels.json').write_text(json.dumps(LABELS, indent=2))
(BUNDLE / 'versions.json').write_text(json.dumps(versions, indent=2))
# PyTorch GPU/CPU wheels differ: record torch version separately, don't pin a CUDA wheel on laptop.
(BUNDLE / 'requirements-inference.txt').write_text('torch>=2.2\\n' + '\\n'.join(
    f'{name}=={version}' for name, version in versions.items() if name != 'torch') + '\\n')
(BUNDLE / 'README.txt').write_text(
    'GuitarSet CNN baseline; not validated for full mixed songs.\\n'
    '24 maj/min classes, no N/silence detection. Unsupported references excluded from metrics.\\n'
    'Keep best.pth, chord_cnn.py and cnn_smoothing.py together. See config.json, labels.json, versions.json.\\n'
    'Install a suitable CPU PyTorch wheel and requirements-inference.txt in a separate environment.\\n'
    'Python usage:\\nfrom chord_cnn import predict_audio\\n'
    "segments = predict_audio('song.wav', 'best.pth', device='cpu')\\n"
    'best.pth stores model_state_dict plus metadata; it is not a bare state_dict.\\n'
    f'SMOKE_TEST={SMOKE_TEST}; best epoch={checkpoint["epoch"]}.\\n'
    'Source: https://zenodo.org/records/3371780 ; cite Xi et al., GuitarSet, ISMIR 2018.\\n', encoding='utf-8')
archive = shutil.make_archive(str(RUN / 'chord_cnn_bundle'), 'zip', BUNDLE)
print('Download:', archive)
display(FileLink(archive))
''')
md('''## Đọc kết quả và bước tiếp
- Train tốt nhưng validation kém: có thể overfit; xem coverage và từng lớp trước.
- Lớp không xuất hiện trong train không thể được kỳ vọng nhận diện đúng.
- Xem `metrics.json`, nghe `example_prediction.json` đối chiếu audio; confidence
  softmax không tự động là xác suất đúng đã hiệu chỉnh.
- Chỉ điều chỉnh bằng train/validation; giữ một benchmark audio thực độc lập.
- Chưa có .pth thật trước khi bạn chạy training. Notebook không hứa một mức accuracy.
- CQT và suy luận CPU trên laptop vẫn có chi phí, nhưng không có backprop/training.

**Trạng thái artifact:** đã kiểm tra cấu trúc/syntax cục bộ; cần chạy trên Kaggle
để xác nhận GPU, bộ dữ liệu thực và kết quả end-to-end.''')

notebook = dict(cells=cells, metadata={'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                                      'language_info': {'name': 'python', 'version': '3.11'}}, nbformat=4, nbformat_minor=5)
for i, cell in enumerate(cells):
    cell['id'] = f'cell-{i:02d}'
output = HERE / 'guitarset_kaggle_train.ipynb'
output.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'Built {output.name}: {len(cells)} cells')
