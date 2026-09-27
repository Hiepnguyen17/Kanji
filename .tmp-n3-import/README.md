# kanji_n3_rich_for_codex

Gói này được chuẩn bị để đưa cho Codex xử lý tiếp trong dự án Kanji của bạn.

## Khác với gói trước
- Không tập trung vào `source URL`.
- Tập trung vào shape dữ liệu mà UI/project thực sự cần.
- Có sẵn scraper để Codex lấy thêm các field chi tiết và ảnh nét viết.

## File chính nên gửi Codex
- `CODEX_IMPORT_RICH_KANJI_N3.md`
- `scrape_kanjikana_n3_rich.py`
- `kanji_n3_project_seed.json`

## Lưu ý
Script scraper được viết theo hướng linh hoạt để Codex có thể chỉnh selector nếu HTML của trang thay đổi đôi chút.
