# Nguồn dữ liệu Kanji

## Danh sách JLPT N5

- Danh sách 80 chữ và thứ tự hiển thị được đối chiếu từ hai trang
  `https://kanjikana.com/vi/kanji/jlpt/n5` và
  `https://kanjikana.com/vi/kanji/jlpt/n5/pages/2`.
- Nghĩa tiếng Việt ngắn và âm Hán Việt được KanjiAI rà soát, biên tập lại;
  không sao chép các danh sách từ thông dụng hoặc bản dịch dài của website.

## Cách đọc và số nét

- KANJIDIC2 của Electronic Dictionary Research and Development Group (EDRDG).
- Trang dự án: `https://www.edrdg.org/kanjidic/kanjd2index_legacy.html`.
- Dữ liệu được sử dụng theo giấy phép của EDRDG; cần giữ ghi công khi phát hành.

Script nhập: `backend/import_kanjikana_n5.py`.

## N3, N2 và N1

- N3: `backend/n3_kanji_full.json` giữ thứ tự từ seed của dự án, metadata ghi là KANJIDIC2-derived; thư mục nhập liệu N3 còn script tham khảo Kanjikana.
- N2: `backend/n2_kanji_full.json` ghi thứ tự từ seed N2 của dự án và quy ước tên SVG KanjiVG. Cần bổ sung tài liệu nguồn chi tiết cho seed và nghĩa/từ liên quan.
- N1: `backend/build_kanji_n1_full.py` ghi rõ danh sách, thứ tự, nghĩa và từ liên quan được lấy/đối chiếu từ trang JLPT N1 của [Kanjikana](https://kanjikana.com/vi/kanji/jlpt/n1); metadata sử dụng bộ dữ liệu KANJIDIC-derived và tên SVG theo KanjiVG.

Việc lưu URL nguồn ở đây phục vụ ghi công, không cần gắn URL vào mỗi mục Kanji trong giao diện. **Chưa xác nhận được điều khoản cho phép tái phân phối phần dữ liệu phái sinh từ Kanjikana**; trước khi phát hành công khai dữ liệu N1/N3 hoặc gói dataset, cần xác minh quyền sử dụng/biên tập lại phần đó hoặc thay bằng nguồn có giấy phép rõ ràng. Việc có đủ trường và SVG không chứng minh quyền tái sử dụng nội dung.

Giấy phép từ điển chính thức của EDRDG: https://www.edrdg.org/edrdg/licence.html (CC BY-SA 4.0 và các điều kiện ghi công bổ sung). KanjiVG: https://kanjivg.tagaini.net/kanjivg/index.html (CC BY-SA 3.0).
