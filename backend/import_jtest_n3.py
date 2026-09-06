"""Import the user-authorized JTest N3 vocabulary curriculum into KanjiAI."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
from urllib.request import Request, urlopen

from database import connect, initialize_database
from import_jtest_n5 import USER_AGENT, VocabularyTableParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SOURCE_ROOT = "https://jtest.net/tu-vung-n3"
OUTLINE = [
    ("人と人との関係", "Quan hệ giữa người với người", ["Gia đình", "Bạn bè và người quen", "Người yêu", "Giao tiếp", "Là người như thế nào?"]),
    ("毎日の暮らし①", "Cuộc sống hàng ngày ①", ["Cách nói về thời gian", "Đời sống ẩm thực", "Dụng cụ và nguyên liệu nấu ăn", "Cách làm món ăn", "Việc nhà"]),
    ("毎日の暮らし②", "Cuộc sống hàng ngày ②", ["Nhà", "Tiền và ngân hàng", "Mua sắm", "Từ sáng đến tối", "Cả những việc như thế này"]),
    ("私たちの町", "Thành phố của chúng tôi", ["Quang cảnh thành phố", "Đi bộ trong thành phố", "Tàu điện và Shinkansen", "Xe buýt", "Lái xe"]),
    ("勉強しよう！", "Học nào", ["Trường học", "Học tập", "Trường đại học của Nhật Bản", "Thi cử", "Hãy cố gắng hơn nữa!"]),
    ("仕事", "Công việc", ["Việc làm", "Công ty", "Quan hệ trên dưới", "Là công việc như thế nào?", "Bằng máy vi tính"]),
    ("楽しいこと", "Những điều vui", ["Du lịch", "Thể thao", "Thời trang", "Ăn diện", "Sở thích"]),
    ("健康のために", "Vì sức khỏe", ["Cơ thể", "Có dấu hiệu gì?", "Triệu chứng", "Không sao chứ?", "Bệnh viện"]),
    ("自然と暮らし", "Tự nhiên và cuộc sống", ["Tự nhiên", "Thời tiết ngày mai", "Ngày nóng và ngày lạnh", "Thay đổi như thế nào?", "Một năm của Nhật Bản"]),
    ("ニュースで学ぼう！", "Hãy học trên bản tin thời sự!", ["Truyền thông đại chúng", "Vụ việc", "Hãy chú ý!", "Rắc rối", "Dữ liệu"]),
    ("気持ちを伝えよう！", "Hãy truyền đạt cảm xúc của mình", ["Tính cách", "Tâm trạng vui mừng", "Tâm trạng buồn chán", "Có cảm giác gì?", "Tâm trạng phức tạp"]),
    ("イメージを伝えよう！", "Hãy truyền đạt ấn tượng của mình", ["Thiết kế", "Ấn tượng về con người", "Ấn tượng về vật", "Xã hội của chúng ta", "Xã hội quốc tế"]),
]


def fetch_lesson(chapter, section):
    request = Request(f"{SOURCE_ROOT}/chapter-{chapter}/section-{section}", headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        document = response.read().decode("utf-8")
    parser = VocabularyTableParser(); parser.feed(document)
    if not parser.rows:
        raise RuntimeError(f"Không đọc được N3 chương {chapter}, bài {section}")
    return chapter, section, parser.rows


def collect_source():
    requested = [(chapter, section) for chapter, (_, _, lessons) in enumerate(OUTLINE, start=1) for section in range(1, len(lessons) + 1)]
    collected = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(fetch_lesson, chapter, section) for chapter, section in requested]
        for future in as_completed(futures):
            chapter, section, rows = future.result(); collected[(chapter, section)] = rows
            print(f"Đã đọc N3 chương {chapter}, bài {section}: {len(rows)} từ")
    return collected


def replace_n3(source_rows):
    initialize_database()
    with connect() as db:
        db.execute("DELETE FROM vocabulary WHERE level='N3'"); db.execute("DELETE FROM vocabulary_staging WHERE level='N3'")
        db.execute("DELETE FROM lessons WHERE level='N3'"); db.execute("DELETE FROM lesson_groups WHERE level='N3'")
        total = lesson_order = 0
        for chapter, (japanese_title, group_title, lesson_titles) in enumerate(OUTLINE, start=1):
            db.execute("INSERT INTO lesson_groups(level,japanese_title,title,description,order_index) VALUES ('N3', ?, ?, ?, ?)", (japanese_title, group_title, f"Chương {chapter} theo lộ trình JTest.", chapter))
            group_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            for section, lesson_title in enumerate(lesson_titles, start=1):
                lesson_order += 1
                db.execute("INSERT INTO lessons(level,title,description,order_index,group_id) VALUES ('N3', ?, ?, ?, ?)", (lesson_title, f"Chương {chapter} · Bài {section} · nguồn JTest", lesson_order, group_id))
                lesson_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                for entry in source_rows[(chapter, section)]:
                    db.execute("""INSERT INTO vocabulary
                        (lesson_id,word,reading,meaning,level,example_japanese,example_reading,example_meaning,audio_url)
                        VALUES (?, ?, ?, ?, 'N3', ?, '', ?, ?)""", (lesson_id, entry["word"], entry["reading"] or entry["word"], entry["meaning"], entry["example_japanese"], entry["example_meaning"], entry["audio_url"]))
                    total += 1
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n3_curriculum_source','jtest')")
    return total


if __name__ == "__main__":
    print(f"Hoàn tất: đã nhập {replace_n3(collect_source())} từ vựng N3 từ JTest.")
