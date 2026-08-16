# KanjiAI

MVP web học Kanji miễn phí với canvas viết tay và API nhận diện tách biệt.

## Chạy giao diện

```powershell
npm install
npm run dev
```

Mở `http://localhost:5173`.

## Chạy API FastAPI

In Command Prompt (CMD):

```bat
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
start-backend.bat
```

In PowerShell, the equivalent is:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8010 --reload
```

API chạy tại `http://localhost:8010`; tài liệu Swagger ở `/docs`.

`POST /api/recognition` hiện là mock có đúng contract nhận ảnh canvas/trả về top-k. Thay phần đánh dấu trong `backend/main.py` bằng pipeline CNN khi đã train ETL9G.

## Thêm dữ liệu qua SQLite

Database tự tạo tại `backend/kanjiai.db` trong lần chạy API đầu tiên. Vào `http://localhost:8010/docs`, dùng `POST /admin/lessons` để tạo bài, sau đó dùng `POST /admin/vocabulary` với `lesson_id` vừa nhận được để thêm từ vựng. `POST /admin/kanji` dùng để thêm Kanji.

Các API `/admin/*` chỉ dành cho môi trường local. Cần thêm JWT trước khi public website.

## Nguồn dữ liệu

Từ vựng mẫu và các định nghĩa được biên soạn từ [JMdict/EDICT của EDRDG](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project), được cấp phép CC BY-SA 4.0. Lộ trình 10 bài N5 trong dự án là cấu trúc học do KanjiAI tự biên soạn.
