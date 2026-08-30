# Huấn luyện nhận diện Kanji N5 — 30 chữ đầu

Model thử nghiệm nhận diện một chữ viết tay, không nhận cả cụm từ. Nhãn gồm:

`一 二 三 四 五 六 七 八 九 十 百 千 円 年 時 分 半 月 火 水 木 金 土 日 人 口 目 耳 手 足`

## Dữ liệu

Tải **ETL9B** từ trang AIST sau khi chủ sở hữu dự án tự đồng ý điều khoản: https://etlcdb.db.aist.go.jp/download2/

Giải nén các file `ETL9B-1` đến `ETL9B-5` vào `backend/data/etl/ETL9B/`. Thư mục này bị Git bỏ qua vì điều khoản ETL không cho phân phối lại dữ liệu.

## Chạy huấn luyện

Từ thư mục dự án, chạy:

```bat
python backend\ml\train_etl9b_n5.py --etl-dir backend\data\etl\ETL9B
```

Model được tạo tại `backend/models/n5_30_kanji.pt`. Model chỉ được dùng sau khi kiểm tra độ chính xác validation; không coi đó là chấm đúng thứ tự nét.
