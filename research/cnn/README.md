# CNN research — train trên Kaggle

**Luồng hiện tại:** dùng `guitarset_kaggle_train.ipynb`, theo hướng dẫn trong
[KAGGLE.md](KAGGLE.md). Toàn bộ tải dữ liệu, tạo CQT và train chạy trên Kaggle.
Laptop chỉ nhận checkpoint để inference. Không cần chạy script local bên dưới.

---

## Ghi chú lịch sử: bước chuẩn bị local ban đầu

Mục tiêu của bước này là lấy và kiểm tra các cặp audio/nhãn trước khi train.
Chưa thay đổi detector, API hoặc dependencies của backend.

## Nguồn dữ liệu

- GuitarSet 1.1.0: https://zenodo.org/records/3371780
- Mô tả: https://guitarset.weebly.com/
- Chọn `audio_mono-mic.zip` (656.9 MB) và `annotation.zip` (39.1 MB).
- Script kiểm tra MD5 do Zenodo công bố trước khi giải nén.
- Dữ liệu và kết quả nằm trong `research/cnn/data/guitarset/`, đã được
  quy tắc `data/` hiện có loại khỏi Git. Cần khoảng 2 GB trống cho zip và giải nén.
- Trước khi huấn luyện/phân phối model, xác nhận giấy phép dataset tại nguồn;
  giấy phép mã nguồn không tự động áp dụng cho audio.

## Chạy từ thư mục gốc Chord AI

Python 3.11 trở lên, chỉ dùng thư viện chuẩn; không cần cài PyTorch ở bước này.

```powershell
python research/cnn/prepare_guitarset.py --download
```

Lệnh tải hai archive, xác minh checksum, giải nén và kiểm tra dữ liệu.
Nếu đã có archive, script xác minh và dùng lại thay vì tải lại.
Nếu tải dở, lần chạy tiếp theo tải lại file đó từ đầu.

Nếu tải thủ công từ Zenodo, đặt nguyên hai file zip vào
`research/cnn/data/guitarset/`, rồi chạy cùng lệnh trên. Khi cả hai checksum
đúng, không cần truy cập mạng. Không dùng file đã đổi tên.

Sau khi đã giải nén, chỉ chạy kiểm tra bằng:

```powershell
python research/cnn/prepare_guitarset.py
```

## Kết quả

- `manifest.json`: đường dẫn audio, thời lượng, sample rate, nhãn theo thời gian
  cùng metadata của cả hai kiểu annotation.
- `audit.json`: số bản ghi, số giờ audio, phân bố nhãn và vấn đề cấu trúc.
- Script yêu cầu đủ 360 cặp, kiểm tra thời gian hữu hạn, đoạn có độ dài dương,
  không chồng lấn và không vượt audio quá 0.1 giây.
- Phân bố nhãn hiện đếm cả hai kiểu annotation, không phải phân bố tập train.
- Hai track `04_BN3-154-E_comp` và `04_Jazz1-200-B_comp` được đánh dấu
  `exclude_pending_review`, theo https://github.com/marl/GuitarSet/issues/5.
  Chưa tự sửa thời gian hoặc loại file gốc.

Đây là kiểm tra cấu trúc; không chứng minh nhãn đúng khi nghe.

## Sau khi audit thành công

1. Nghe vài đoạn cùng annotation, chọn rõ kiểu `performed` hay `instructed`.
2. Chốt quy tắc quy đổi nhãn; không đổi hợp âm không hỗ trợ thành `N`.
3. Thiết kế train/validation/test theo nhóm bản ghi/bài mẫu; các phiên bản
   cùng nguồn phải ở cùng tập. GuitarSet có nhiều người chơi cùng lead sheet,
   nên chia ngẫu nhiên từng frame sẽ cho kết quả quá lạc quan.
4. Tạo đặc trưng CQT, train CNN nhỏ và so sánh với DSP trên cùng tập test.
5. Đánh giá riêng trên nhạc phối nhiều nhạc cụ trước khi tích hợp vào ứng dụng.

## Trạng thái lần chuẩn bị đầu

Script đã được tạo. Mạng trong sandbox bị chặn và yêu cầu quyền tải đã bị từ
chối, nên chưa tải GuitarSet, chưa audit dữ liệu thực và chưa train CNN.
Python hệ thống là 3.12.7; `.venv` hiện có không chạy được vì interpreter gốc
không còn ở đường dẫn đã cấu hình. Bước này không cần sửa môi trường backend.
