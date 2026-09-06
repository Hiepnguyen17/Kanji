"""Import the user-authorized JTest N4 vocabulary curriculum into KanjiAI."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
from urllib.request import Request, urlopen

from database import connect, initialize_database
from import_jtest_n5 import USER_AGENT, VocabularyTableParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SOURCE_ROOT = "https://jtest.net/tu-vung-n4"
OUTLINE = [
    ("私たちの毎日", "Mỗi ngày của chúng tôi", ["Thời gian", "Gia đình", "Nhà", "Phòng", "Từ sáng đến tối"]),
    ("勉強と仕事", "Việc học và công việc", ["Trường học", "Trường đại học", "Việc học", "Công việc ①", "Công việc ②"]),
    ("楽しいこと", "Những việc vui vẻ", ["Du lịch", "Món ăn ~ Ăn", "Món ăn ~ Nấu (Làm)", "Đi chợ, mua sắm", "Nơi, chỗ"]),
    ("出かけよう！", "Hãy đi ra ngoài nào", ["Thời tiết", "Tự nhiên", "Phương tiện giao thông", "Lái xe (xe, tàu)", "Thế giới"]),
    ("人と人との関係", "Mối quan hệ giữa người với người", ["Giao tiếp", "Người yêu", "Những rắc rối", "Sở thích", "Thể thao"]),
    ("けんこうとようす", "Sức khỏe và trạng thái", ["Cơ thể / Sức khỏe", "Đau ốm / Bị thương", "Thời trang", "Trạng thái, tình trạng ①", "Trạng thái, tình trạng ②"]),
    ("いつ？どこで？", "Khi nào? Tại đâu?", ["Tin tức", "Lời hứa", "Cảm giác", "Hãy ghi nhớ cả phó từ ①", "Hãy ghi nhớ cả phó từ ②", "Hãy ghi nhớ cả từ nối!"]),
]


def fetch_lesson(chapter, section):
    request = Request(f"{SOURCE_ROOT}/chapter-{chapter}/section-{section}", headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        document = response.read().decode("utf-8")
    parser = VocabularyTableParser()
    parser.feed(document)
    if not parser.rows:
        raise RuntimeError(f"Không đọc được N4 chương {chapter}, bài {section}")
    return chapter, section, parser.rows


def collect_source():
    requested = [(chapter, section) for chapter, (_, _, lessons) in enumerate(OUTLINE, start=1) for section in range(1, len(lessons) + 1)]
    collected = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(fetch_lesson, chapter, section) for chapter, section in requested]
        for future in as_completed(futures):
            chapter, section, rows = future.result()
            collected[(chapter, section)] = rows
            print(f"Đã đọc N4 chương {chapter}, bài {section}: {len(rows)} từ")
    return collected


def replace_n4(source_rows):
    initialize_database()
    with connect() as db:
        db.execute("DELETE FROM vocabulary WHERE level='N4'")
        db.execute("DELETE FROM vocabulary_staging WHERE level='N4'")
        db.execute("DELETE FROM lessons WHERE level='N4'")
        db.execute("DELETE FROM lesson_groups WHERE level='N4'")
        total = 0
        lesson_order = 0
        for chapter, (japanese_title, group_title, lesson_titles) in enumerate(OUTLINE, start=1):
            db.execute("INSERT INTO lesson_groups(level,japanese_title,title,description,order_index) VALUES ('N4', ?, ?, ?, ?)", (japanese_title, group_title, f"Chương {chapter} theo lộ trình JTest.", chapter))
            group_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            for section, lesson_title in enumerate(lesson_titles, start=1):
                lesson_order += 1
                db.execute("INSERT INTO lessons(level,title,description,order_index,group_id) VALUES ('N4', ?, ?, ?, ?)", (lesson_title, f"Chương {chapter} · Bài {section} · nguồn JTest", lesson_order, group_id))
                lesson_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                for entry in source_rows[(chapter, section)]:
                    db.execute("""INSERT INTO vocabulary
                        (lesson_id,word,reading,meaning,level,example_japanese,example_reading,example_meaning,audio_url)
                        VALUES (?, ?, ?, ?, 'N4', ?, '', ?, ?)""", (lesson_id, entry["word"], entry["reading"] or entry["word"], entry["meaning"], entry["example_japanese"], entry["example_meaning"], entry["audio_url"]))
                    total += 1
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n4_curriculum_source','jtest')")
    return total


if __name__ == "__main__":
    print(f"Hoàn tất: đã nhập {replace_n4(collect_source())} từ vựng N4 từ JTest.")
