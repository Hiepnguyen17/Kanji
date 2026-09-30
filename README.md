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

## Kiểm thử

```powershell
\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
npm run test
```

Lệnh này kiểm tra API công khai và khóa admin, migration SQLite từ schema cũ,
dữ liệu ngữ pháp N5–N1, và quy tắc render chip công thức ngữ pháp.

## Cấu hình API

Frontend chỉ dùng `VITE_API_BASE_URL`; không ghi cứng địa chỉ API trong từng màn hình. Backend chỉ cho các origin trong `KANJIAI_CORS_ORIGINS` gọi API.

Khi cần frontend chạy ở host/cổng khác, tạo `backend/.env` từ `backend/.env.example`, rồi đặt các origin cách nhau bằng dấu phẩy. Ví dụ:

```text
KANJIAI_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.20:5173
```

Khởi động lại API sau khi đổi cấu hình. Các file `.env` không được đưa lên Git.

## Triển khai Docker qua Cloudflare Tunnel

Bản production chạy React qua Nginx và chuyển các đường dẫn API về FastAPI trong
cùng một domain. SQLite được lưu trong Docker volume `kanjiai_data`, không nằm
trong image hay Git repository. Cloudflare Tunnel tạo kết nối **đi ra ngoài** từ
VPS; vì vậy bản này hoạt động cả với VPS NAT không có cổng public 80/443.

1. Thêm domain vào Cloudflare, thay nameserver ở nhà đăng ký bằng hai nameserver
   Cloudflare cấp và chờ zone có trạng thái **Active**.
2. Trong Cloudflare, vào **Networking → Tunnels**, tạo remotely-managed tunnel
   tên `kanjiai-vps`. Ở phần public hostname, chọn domain `kanjiai.online`, để
   trống subdomain và đặt **Service URL** là `http://web:80`.
3. Sao chép `deploy/.env.production.example` thành `deploy/.env.production`,
   điền domain, Google OAuth, API admin key và tunnel token. Token là bí mật;
   không đưa lên GitHub hoặc gửi qua chat.

```bash
cp deploy/.env.production.example deploy/.env.production
nano deploy/.env.production
docker compose --env-file deploy/.env.production up -d --build
docker compose ps
```

Không cần Caddy, IP public, bản ghi `A` hay mở cổng 80/443. Sau khi deploy,
Google OAuth callback phải là:

```text
https://kanjiai.online/auth/google/callback
```

Thêm chính xác URL này vào **Authorized redirect URIs** trong Google Cloud
Console. Kiểm tra service tại `https://kanjiai.online/health`.

### Backup SQLite

Chạy lệnh sau trên VPS để tạo snapshot nhất quán khi API đang hoạt động:

```bash
sh deploy/backup-sqlite.sh
```

File backup được tạo trong `backups/` và bị Git bỏ qua. Script kiểm tra SQLite
sau khi sao lưu rồi giữ **14 bản gần nhất** (đổi bằng `KANJIAI_BACKUP_KEEP`).
Backup trên cùng VPS **không đủ** để khôi phục nếu mất máy chủ; cần sao chép một
bản ra máy riêng. Không sao chép thư mục
`backend/data/local/` hay `deploy/.env.production` lên GitHub.

Trước khi đưa domain vào sử dụng, kiểm tra biến production mà không làm lộ
secret:

```bash
sh deploy/verify-production.sh
```

Sau khi kiểm tra đạt, cài cron backup mỗi ngày lúc **03:15 theo giờ VPS**:

```bash
sh deploy/install-backup-cron.sh
crontab -l
```

Sau lần chạy cron đầu tiên, **xác nhận bằng file thực và log**:

```bash
crontab -l | grep 'KanjiAI SQLite backup'
ls -lt backups/kanjiai-*.db | head
tail -n 30 backups/backup-cron.log
```

Kiểm tra và phục hồi thử **vào một file khác**, tuyệt đối không ghi đè
`/data/kanjiai.db` đang chạy:

```bash
python3 deploy/verify_backup.py --backup backups/kanjiai-YYYYMMDDTHHMMSSZ.db --restore-to /tmp/kanjiai-restore-test.db
```

Thay tên file bằng bản backup thực. Lệnh từ chối ghi đè nếu file đích đã có.
Trên máy Windows có OpenSSH, lấy bản mới nhất ra thư mục **ngoài repository**
(SSH/SCP sẽ hỏi mật khẩu nếu chưa cấu hình khóa):

```powershell
.\deploy\download-latest-backup.ps1 -DestinationDirectory D:\KanjiAI-backups
```

File tải về được kiểm tra `PRAGMA integrity_check` và các bảng thiết yếu.
Không lưu backup chứa dữ liệu tài khoản lên GitHub hay kho công khai.

Đổi giờ chạy khi cần (ví dụ 02:30) bằng:

```bash
KANJIAI_BACKUP_CRON='30 2 * * *' sh deploy/install-backup-cron.sh
```

Ví dụ chỉ giữ 7 bản trên VPS: `KANJIAI_BACKUP_KEEP=7 sh deploy/install-backup-cron.sh`.

## Kiểm tra nội dung và trang giới thiệu

- `/about` trình bày chức năng đã có, chức năng chưa làm, nguồn dữ liệu và dữ liệu tài khoản được lưu.
- `python deploy/audit_content.py --db backend/kanjiai.db --svg-root public/kanjivg` rà các trường/ví dụ/SVG còn thiếu mà không đọc dữ liệu người học.
- Xem kết quả rà local và giới hạn kiểm tra tại [CONTENT_AUDIT.md](CONTENT_AUDIT.md).
## Đăng nhập Google và tiến độ học

Ứng dụng dùng Google OAuth theo luồng mở cửa sổ chọn tài khoản, giống màn hình Google trong ảnh tham khảo. Lần đầu đăng nhập sẽ tự tạo tài khoản; cookie phiên chỉ được lưu ở API, còn tiến độ Kanji/từ vựng/ngữ pháp nằm trong SQLite theo từng tài khoản.

1. Vào [Google Cloud Console](https://console.cloud.google.com/), tạo project và màn hình đồng ý OAuth.
2. Tạo **OAuth client ID** loại **Web application**.
3. Trong **Authorized redirect URIs**, thêm chính xác `http://localhost:8010/auth/google/callback` khi chạy local.
4. Sao chép `backend/.env.example` thành `backend/.env`, rồi điền `GOOGLE_CLIENT_ID` và `GOOGLE_CLIENT_SECRET` (không đưa tệp này lên Git).
5. Khởi động lại backend và nhấn **Đăng nhập bằng Google** trong ứng dụng.

Khi triển khai thật, thay `GOOGLE_REDIRECT_URI`, `KANJIAI_APP_URL`, `KANJIAI_CORS_ORIGINS` bằng các URL HTTPS thật và đăng ký đúng redirect URI đó trong Google Cloud Console.

## Tạo phiếu học để in / lưu PDF

Mở **Tạo phiếu học** trên thanh điều hướng (`/worksheets`), hoặc dùng nút ở
ngày học Kanji, bài từ vựng và tab Kanji/Từ vựng trong danh sách ôn tập.
Nguồn bài học dùng được khi chưa đăng nhập; nguồn ôn tập yêu cầu tài khoản.

- Luyện viết Kanji: chữ mẫu có số nét, các bước nét từ SVG KanjiVG, ô tô mờ và ô tự viết.
- Luyện viết từ vựng: từ, cách đọc, nghĩa, ví dụ nếu có và dòng tự đặt câu.
- Tự kiểm tra từ vựng: điền cách đọc/nghĩa hoặc viết từ từ gợi ý; có thể đảo đề và thêm đáp án riêng ở cuối.

Chọn tối đa 100 mục/lần, cỡ ô 10/12/15 mm, bật/tắt cách đọc và ví dụ.
Trang A4 được phân theo chiều cao thực tế, mỗi khối từ/chữ giữ nguyên trên một trang.
Chọn **In / Lưu PDF**, khổ A4, tỷ lệ 100%, tắt đầu/chân trang trình duyệt;
chọn **Lưu dưới dạng PDF** nếu không in giấy. Không cần API AI hay dịch vụ tạo PDF.
Tạo/in phiếu không ghi tiến độ học. SVG thiếu được thông báo và thay bằng chữ mẫu.

## Nhận diện viết tay

`POST /api/recognition` nhận ảnh canvas hoặc mảng nét, với `language` là `ja` hoặc `zh`, và trả tối đa ba dự đoán có độ tin cậy. Trạng thái model có thể kiểm tra qua:

- `GET /health` — tổng quan database và model Nhật.
- `GET /api/handwriting/status` — model Nhật cùng dữ liệu mẫu viết.

Nếu màn hình báo thiếu phụ thuộc AI, cài lại `backend/requirements-ml.txt` trong đúng môi trường `.venv`. Nếu báo thiếu model, kiểm tra các file ONNX trong `backend/models/dakanji/` hoặc `backend/models/hanzi/`.

## Dữ liệu local

Database mặc định là `backend/kanjiai.db`. Bản này chỉ chứa dữ liệu nội dung
(Kanji, từ vựng và ngữ pháp), tuyệt đối không chứa tài khoản, phiên đăng nhập,
tiến độ, danh sách ôn tập hoặc cài đặt cá nhân.

Để dùng dữ liệu kiểm thử cá nhân, đặt một database SQLite ở thư mục đã bị Git
bỏ qua, ví dụ `backend/data/local/kanjiai.test.db`, rồi thêm vào `backend/.env`:

```text
KANJIAI_DB_PATH=data/local/kanjiai.test.db
```

Không đặt biến này trên production nếu muốn dùng database nội dung sạch mặc
định. Khi chạy với database trống, API sẽ tự khởi tạo schema và dữ liệu seed.

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
- Một phần danh sách/từ liên quan JLPT đã được tham khảo từ Kanjikana; xem [KANJI_SOURCES.md](KANJI_SOURCES.md) để biết phạm vi và phần quyền tái sử dụng còn cần xác minh trước khi tái phân phối dataset.
