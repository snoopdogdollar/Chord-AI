# Train CNN trên Kaggle

Import **guitarset_kaggle_train.ipynb** vào notebook Kaggle. File tự chứa toàn bộ
code và giải thích tiếng Việt theo cách tiếp cận image classification.

**Nếu Kaggle từ chối ký tự `#`:** upload file
`data/kaggle_upload/guitarset_kaggle.zip` đã chuẩn bị từ hai archive gốc.
Tên bên trong đã đổi `#` thành `sharp` ở cả audio và JAMS; nội dung giữ nguyên.
Chỉ gắn bản này vào Input, không gắn đồng thời bản gốc. Notebook hiện tại hỗ trợ
cả ZIP này và dữ liệu Kaggle đã tự giải nén. Dùng lại notebook mới sau cập nhật.

1. Bật GPU accelerator; notebook dừng nếu không ở Kaggle hoặc thiếu GPU.
2. Bật Internet để tải GuitarSet trực tiếp trên Kaggle (~696 MB), hoặc thêm Input
   chứa `annotation.zip` + `audio_mono-mic.zip`. Cũng hỗ trợ dữ liệu giải nén
   có `.jams` và `*_mic.wav`. Chỉ gắn một bản để tránh trùng track ID.
3. Chạy từng cell, nghe audio và xem annotation/CQT ở bước 5.
4. Có thể chạy `SMOKE_TEST=True` (2 epoch) để kiểm tra luồng, rồi đổi False và
   chạy lại từ đầu để train tối đa 35 epoch, early stopping sau 6 epoch.
5. Lưu phiên bản có output và tải `chord_cnn_bundle.zip` từ output notebook.

Bundle gồm `best.pth`, `chord_cnn.py`, cấu hình CQT, thứ tự nhãn, phiên bản thư
viện, split manifest, metrics, biểu đồ loss/accuracy, confusion matrix và dự đoán mẫu.

## Từ ảnh sang audio

- Input `[1,84,43]`: một kênh, 84 bin cao độ, 43 frame thời gian, khoảng 1 giây.
- Nhãn ở tâm cửa sổ; cửa sổ cách nhau khoảng 116 ms.
- Không cần chuyển CQT thành PNG; CNN nhận ma trận số trực tiếp.
- Không flip/rotate như ảnh. Chia nhóm bài trước khi cắt cửa sổ để tránh leakage.
- CQT chạy CPU Kaggle, training chạy GPU Kaggle; không train trên laptop.

## Phạm vi

24 lớp trưởng/thứ. Quy đổi hợp âm mở rộng theo bảng trong `reduce_chord`.
N/X/sus/dim/aug và nhãn không hỗ trợ bị bỏ khỏi loss/metric. Chưa có no-chord
hay silence detection; inference luôn chọn một trong 24 lớp.
Notebook báo coverage, nhãn bỏ qua và lớp thiếu trong train.

Split theo style/progression, giữ chung các tempo, key, người chơi và comp/solo.
Các style vẫn có progression chung; đây chưa phải đánh giá trên progression mới
hoàn toàn hoặc nhạc phối nhiều nhạc cụ. Metric chấm các tâm cửa sổ hợp lệ,
không phải CSR toàn bài; cần benchmark chung để so với DSP.

Nhãn dùng inferred/performed, thứ hai trong các chord annotation theo mirdata.
Loại cả cặp comp/solo của hai bản ghi có lỗi timing đã biết, không sửa nguồn.
Chọn best checkpoint bằng validation loss, test chỉ chạy ở cuối.

## Inference sau khi tải về

Máy hiện tại dùng môi trường riêng `D:\chord-cnn-env`. Project vẫn trên C.
Chạy kiểm tra checkpoint và đoạn rock 10–40 giây từ thư mục project:

```powershell
.\research\cnn\run_cpu_check.ps1
```

Script dùng hai luồng CPU, đặt cache/tạm trong `D:\chord-cnn-temp` và kết quả
ở `D:\chord-cnn-results\rock_10_40`. Không train và không cần activate venv.
Môi trường này sử dụng Python nền của runtime desktop; nếu runtime nền bị gỡ,
có thể cần tạo lại venv bằng Python Windows độc lập. Venv cũ ở C không bị xóa.

Cài PyTorch CPU phù hợp và thư viện trong `requirements-inference.txt` của bundle
vào môi trường riêng. Không cần CUDA trên laptop. Trong thư mục giải nén:

```python
from chord_cnn import predict_audio
segments = predict_audio('song.wav', 'best.pth', device='cpu')
```

Checkpoint chứa `model_state_dict` và metadata, không phải state_dict trần.
Kiến trúc và preprocessing được đóng gói cùng weights. Chưa lưu optimizer để
resume training. Suy luận/CQT trên CPU vẫn có chi phí, nhưng không có backprop.

## File và kiểm tra

- `chord_cnn.py`: kiến trúc + CQT + inference, được nhúng nguyên bản vào notebook.
- `build_notebook.py`: tạo lại notebook bằng Python chuẩn, không tải/train.
- `test_notebook_contract.py`: kiểm tra syntax, nhãn và nhóm bằng stdlib.
- `prepare_guitarset.py`: script local cũ, không cần chạy cho Kaggle.

```powershell
python research/cnn/build_notebook.py
python -m unittest discover -s research/cnn -p test_notebook_contract.py -v
```

Đã kiểm tra syntax/contract cục bộ; chưa chạy dữ liệu thực hoặc GPU trên Kaggle.
Không có checkpoint thật trước khi chạy training. Backend chưa thay đổi.

Nguồn và trích dẫn có trong notebook, gồm GuitarSet 1.1.0 trên Zenodo,
Xi et al., ISMIR 2018, tài liệu mirdata, librosa và PyTorch.
