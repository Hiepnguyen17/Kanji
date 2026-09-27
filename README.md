# KanjiAI

Ứng dụng học Kanji gồm giao diện React/Vite và API FastAPI. Canvas viết tay gửi ảnh/nét vẽ đến **model thật** chạy cục bộ:

- Nhật: DaKanji v2 ONNX (Dariyooo / DaAppLab, MIT), có phương án dự phòng là CNN N5 tự huấn luyện nếu có checkpoint.
- Trung: model Hanzi ONNX do KanjiAI huấn luyện từ CASIA-HWDB.

Nhận diện dành cho **một chữ** mỗi lần; đây không phải công cụ chấm đúng/sai thứ tự nét.

## Yêu cầu

- Node.js 20+ và npm
- Python 3.10+
- Windows: khuyến nghị PowerShell hoặc CMD

Các model ONNX Nhật/Trung được lưu trong `backend/models/`. Nếu thiếu file model, API vẫn khởi động nhưng endpoint nhận diện sẽ trả trạng thái thiếu model/phụ thuộc thay vì giả lập kết quả.

## Chạy ở máy local

Mở hai terminal tại thư mục dự án `D:\B\KanjiAI`.

### 1. API và model nhận diện

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-ml.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host localhost --port 8010 --reload
```

Hoặc chạy `start-backend.bat` sau khi đã cài phụ thuộc.

Kiểm tra API tại:

- Health/model: [http://127.0.0.1:8010/health](http://127.0.0.1:8010/health)
- Swagger: [http://127.0.0.1:8010/docs](http://127.0.0.1:8010/docs)

`backend/requirements.txt` chỉ gồm API cơ bản. `backend/requirements-ml.txt` bao gồm cả API lẫn NumPy, Pillow, PyTorch và ONNX Runtime — dùng file này khi cần nhận diện viết tay.

### 2. Giao diện

```powershell
Copy-Item .env.example .env.local
npm install
npm run dev
```

Mở [http://localhost:5173](http://localhost:5173). Biến `VITE_API_BASE_URL` trong `.env.local` cho phép đổi URL API; mặc định là `http://localhost:8010`.

## Cấu hình API

Frontend chỉ dùng `VITE_API_BASE_URL`; không ghi cứng địa chỉ API trong từng màn hình. Backend chỉ cho các origin trong `KANJIAI_CORS_ORIGINS` gọi API.

Khi cần frontend chạy ở host/cổng khác, tạo `backend/.env` từ `backend/.env.example`, rồi đặt các origin cách nhau bằng dấu phẩy. Ví dụ:

```text
KANJIAI_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.20:5173
```

Khởi động lại API sau khi đổi cấu hình. Các file `.env` không được đưa lên Git.

## Đăng nhập Google và tiến độ học

Ứng dụng dùng Google OAuth theo luồng mở cửa sổ chọn tài khoản, giống màn hình Google trong ảnh tham khảo. Lần đầu đăng nhập sẽ tự tạo tài khoản; cookie phiên chỉ được lưu ở API, còn tiến độ Kanji/từ vựng/ngữ pháp nằm trong SQLite theo từng tài khoản.

1. Vào [Google Cloud Console](https://console.cloud.google.com/), tạo project và màn hình đồng ý OAuth.
2. Tạo **OAuth client ID** loại **Web application**.
3. Trong **Authorized redirect URIs**, thêm chính xác `http://localhost:8010/auth/google/callback` khi chạy local.
4. Sao chép `backend/.env.example` thành `backend/.env`, rồi điền `GOOGLE_CLIENT_ID` và `GOOGLE_CLIENT_SECRET` (không đưa tệp này lên Git).
5. Khởi động lại backend và nhấn **Đăng nhập bằng Google** trong ứng dụng.

Khi triển khai thật, thay `GOOGLE_REDIRECT_URI`, `KANJIAI_APP_URL`, `KANJIAI_CORS_ORIGINS` bằng các URL HTTPS thật và đăng ký đúng redirect URI đó trong Google Cloud Console.

## Nhận diện viết tay

`POST /api/recognition` nhận ảnh canvas hoặc mảng nét, với `language` là `ja` hoặc `zh`, và trả tối đa ba dự đoán có độ tin cậy. Trạng thái model có thể kiểm tra qua:

- `GET /health` — tổng quan database và model Nhật.
- `GET /api/handwriting/status` — model Nhật cùng dữ liệu mẫu viết.

Nếu màn hình báo thiếu phụ thuộc AI, cài lại `backend/requirements-ml.txt` trong đúng môi trường `.venv`. Nếu báo thiếu model, kiểm tra các file ONNX trong `backend/models/dakanji/` hoặc `backend/models/hanzi/`.

## Dữ liệu local

SQLite tự tạo tại `backend/kanjiai.db` khi API chạy lần đầu.

## Quản trị nội dung an toàn

Mọi API `/admin/*` đều bị khóa mặc định. Trước khi dùng, tạo một chuỗi ngẫu nhiên dài ít nhất 32 ký tự, đặt trong `backend/.env` rồi khởi động lại backend:

```text
KANJIAI_ADMIN_API_KEY=chuoi-bi-mat-dai-va-ngau-nhien
```

Gửi khóa qua HTTP header `X-Admin-Key` — không đưa khóa vào frontend, Git hay ảnh chụp màn hình. Nếu biến chưa có, API quản trị trả `503`; nếu khóa sai, trả `401`.

Các thao tác sẵn có:

- `GET /admin/content-audit`: liệt kê Kanji, từ vựng, ví dụ N5 và ngữ pháp còn thiếu.
- `PATCH /admin/kanji/{char}`, `/admin/lessons/{id}`, `/admin/vocabulary/{id}`, `/admin/grammar/patterns/{id}`: sửa trực tiếp một mục.
- `POST /admin/maintenance/reconcile`: chạy lại các nhập liệu/đối soát có tính lặp an toàn. Lệnh này không xóa `users`, `user_sessions` hoặc `user_progress`; phản hồi trả số tiến độ trước/sau để kiểm tra.

Ví dụ kiểm tra mục thiếu bằng PowerShell:

```powershell
Invoke-RestMethod http://localhost:8010/admin/content-audit -Headers @{ 'X-Admin-Key' = $env:KANJIAI_ADMIN_API_KEY }
```

## Nguồn dữ liệu và ghi nhận

- Từ vựng/định nghĩa tham khảo [JMdict/EDICT của EDRDG](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project), CC BY-SA 4.0.
- SVG thứ tự nét: KanjiVG.
- Nhận diện Nhật: DaKanji v2, Dariyooo / DaAppLab, MIT.
- Dữ liệu huấn luyện Trung: CASIA-HWDB; chỉ model đã huấn luyện được dùng khi giấy phép dữ liệu không cho phân phối dataset.
