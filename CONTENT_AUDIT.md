# Kiểm tra nội dung KanjiAI

Kiểm tra ngày 30/09/2026 trên `backend/kanjiai.db` **local**, không phải database đang chạy trên VPS:

| Nội dung | Tổng số | Thiếu trường chính | Thiếu ví dụ | Thiếu SVG nét viết |
| --- | ---: | ---: | ---: | ---: |
| Kanji | 2.136 | 0 | — | 0 |
| Từ vựng | 7.058 | 0 | 0 | — |
| Mẫu ngữ pháp | 595 | 0 | 0 | — |

Trường chính được kiểm tra: Kanji có nghĩa, âm Hán Việt, bộ thủ, số nét và ít nhất một cách đọc; từ vựng có chữ, cách đọc, nghĩa; ngữ pháp có công thức và giải thích. Ví dụ từ vựng cần câu tiếng Nhật và nghĩa; ví dụ ngữ pháp cần ít nhất một bản ghi. SVG được đối chiếu theo tên Unicode trong `public/kanjivg`, parse được và có ít nhất một đường nét (`path`).

Chạy lại (chỉ đọc):

```bash
python deploy/audit_content.py --db backend/kanjiai.db --svg-root public/kanjivg
```

Kết quả 0 mục thiếu chỉ chứng minh các trường hiện diện, **không** xác nhận mọi nghĩa, ví dụ hay nét viết đều chính xác về mặt học thuật. Cần biên tập/đối chiếu mẫu để kiểm tra chất lượng nội dung. Để kiểm tra dữ liệu production, tải một bản backup an toàn về máy riêng rồi chạy cùng lệnh với `--db` trỏ tới bản backup đó.
