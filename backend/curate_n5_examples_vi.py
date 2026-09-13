"""Replace source N5 example translations with KanjiAI-authored Vietnamese examples."""
import argparse
import json
import sqlite3
from pathlib import Path

from database import DB_PATH

MEANINGS = [
    "Đây là sách.", "Đây là sách. (cách nói thân mật)", "Hôm qua là chủ nhật.", "Đây không phải là bút.",
    "Mỗi sáng tôi uống cà phê.", "Hôm qua tôi đã xem phim.", "Tôi không uống rượu.", "Hôm qua tôi đã không làm bài tập.",
    "Tôi là học sinh/sinh viên.", "Ai đã đến?", "Tôi đọc sách.", "Tôi viết thư cho bạn.",
    "Tôi đi học bằng xe buýt.", "Tôi đã mua bánh mì và sữa.", "Đây là sách của tôi.", "Tôi đi đến trường.",
    "Tôi đến từ Nhật Bản.", "Tôi đi bộ đến ga.", "Tôi cũng là học sinh/sinh viên.", "Đây là gì?",
    "Hôm nay thời tiết đẹp nhỉ.", "Cửa hàng kia rẻ đấy.", "Đây là sách.", "Quyển sách này đắt.",
    "Đây là trường học.", "Có một quyển sách trên bàn.", "Có một con chó trong vườn.", "Mỗi sáng tôi uống cà phê rồi đọc báo.",
    "Hãy nói chậm thôi.", "Bây giờ tôi đang đọc sách.", "Hôm nay tôi không đi học.", "Hôm qua tôi đã xem phim.",
    "Quyển sách này đắt.", "Quyển sách này không đắt.", "Hôm qua trời lạnh.", "Phòng này yên tĩnh.",
    "Tôi muốn một căn phòng yên tĩnh.", "Phòng này không yên tĩnh.", "Thị trấn đó rất yên tĩnh.", "Chúng ta cùng đi nhé.",
    "Chúng ta uống trà nhé?", "Tôi muốn đi Nhật Bản.", "Tôi muốn một chiếc xe mới.", "Chó to hơn mèo.",
    "Núi Phú Sĩ là ngọn núi cao nhất Nhật Bản.", "Cho tôi ba quả táo.", "Gia đình tôi có bốn người.", "Đây là gì?",
    "Xin đừng chụp ảnh ở đây.", "Tôi đã mua rau, trái cây và vài thứ khác ở siêu thị.", "Bạn có muốn cùng xem phim không?", "Tôi đã làm bài tập rồi.",
    "Tôi vẫn chưa làm bài tập.", "Khi còn nhỏ, tôi thường chơi ở công viên.", "Tôi đã xem phim cùng bạn.", "Tôi chỉ uống nước.",
    "Hãy dậy sớm.", "Hãy giữ yên lặng.", "Quyển sách này đắt và nặng.", "Căn phòng này yên tĩnh và đẹp.",
    "Tôi thích cả cà phê lẫn trà.", "Tôi đã mua táo và chuối.", "Có một quyển sách trên bàn.", "Có mấy quả táo?",
    "Cái này bao nhiêu tiền?", "Bây giờ là mấy giờ?", "Hôm nay là thứ mấy?", "Bây giờ là ba giờ.",
    "Hãy đợi mười phút.", "Tôi 20 tuổi.", "Chiếc bánh này giá 500 yên.", "Tôi đã mua ba chiếc bút chì.",
    "Cho tôi ba tờ giấy.", "Mỗi ngày tôi uống cà phê.", "Mỗi ngày tôi học hai giờ.", "Quyển sách này đắt.",
    "Vì không có thời gian nên tôi vội.",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    if len(entries) != len(MEANINGS):
        raise ValueError("Source N5 count changed; review Vietnamese examples.")
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM grammar_examples WHERE pattern_id IN (SELECT p.id FROM grammar_patterns p JOIN grammar_lessons l ON l.id=p.lesson_id WHERE l.level='N5')")
        for entry, meaning in zip(entries, MEANINGS):
            pattern = db.execute("""SELECT p.id FROM grammar_patterns p JOIN grammar_lessons l ON l.id=p.lesson_id
                WHERE l.level='N5' AND p.formula=?""", (entry["pattern"],)).fetchone()
            db.execute("INSERT INTO grammar_examples(pattern_id,japanese,reading,meaning_vi) VALUES (?,?,?,?)", (pattern[0], entry["examples"][0]["japanese"], "", meaning))
    print(f"Curated {len(entries)} N5 examples with Vietnamese meanings.")

if __name__ == "__main__":
    main()
