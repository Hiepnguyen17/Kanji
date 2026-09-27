# Hướng dẫn cho Codex: tích hợp dữ liệu Kanji N3 giàu thông tin

Mục tiêu: dự án không chỉ cần danh sách `kanji + meaning`, mà còn cần các trường phục vụ UI như trong ảnh mẫu:
- ảnh nét viết / stroke-order image
- số nét
- âm On / Kun
- bộ thủ
- từ vựng liên quan
- kanji liên quan
- tag JLPT / chủ đề / Kanken nếu có

## File trong gói này
1. `kanji_n3_project_seed.json`
   - seed ban đầu gồm 370 Kanji N3.
   - KHÔNG giữ `source URL` trong output.
   - Có sẵn cấu trúc field theo hướng dự án.
2. `kanji_project_schema_example.json`
   - ví dụ shape mong muốn cho 1 kanji.
3. `scrape_kanjikana_n3_rich.py`
   - script để scrape đầy đủ thông tin từ Kanjikana và tải ảnh nét viết về local assets.

## Việc cần làm trong dự án
1. Đọc cấu trúc dữ liệu Kanji hiện có trong dự án.
2. Chạy scraper để lấy full data N3 và tải ảnh vào thư mục asset phù hợp.
3. Map dữ liệu vào schema của dự án.
4. Không lưu `source_list_url` / `source_detail_url` vào dữ liệu cuối cùng.
5. Nếu dự án đã có Kanji trùng:
   - không tạo duplicate,
   - update field còn thiếu nếu hợp lý.
6. Nếu dự án đang dùng thư mục public/static/assets cho ảnh, đổi `strokeImage.relativePath` về đúng convention hiện có.
7. Giữ dữ liệu theo hướng UI thực tế:
   - hero card: `kanji`, `meaning`, `jlpt`, `strokeCount`
   - box On/Kun: `onReadings`, `kunReadings`
   - box Bộ thủ: `radicals`
   - Từ vựng liên quan: `commonWords`
   - Kanji liên quan: `relatedKanji`
   - ảnh viết: `strokeImage.relativePath`

## Kết quả mong muốn
- 370 Kanji N3 được import vào dự án.
- Có ảnh stroke-order local.
- UI detail Kanji hiển thị đủ dữ liệu cần thiết.
- Không còn giữ các field URL nguồn trong dữ liệu final.
- Build/test/lint vẫn pass.

## Gợi ý quy trình
1. Chạy:
   ```bash
   python scrape_kanjikana_n3_rich.py --output kanji_n3_project_full.json --assets-dir public/assets/kanji/strokes
   ```
2. Viết script import/seed hoặc chỉnh file data có sẵn.
3. Chạy kiểm tra duplicate theo `kanji`.
4. Chạy build/test/lint.
5. Báo cáo file nào đã được sửa.
