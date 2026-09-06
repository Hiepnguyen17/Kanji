"""One-time importer for the N5 course the user is licensed to reuse from JTest.

Run from the project root with:
    .venv\Scripts\python.exe backend\import_jtest_n5.py

The importer deliberately retains the source's word-audio URL for each card.
It only replaces N5 vocabulary, lesson groups and lessons; Kanji, grammar and
learner handwriting samples are untouched.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
import sys
from urllib.request import Request, urlopen

from database import connect, initialize_database

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SOURCE_ROOT = "https://jtest.net/tu-vung-n5"
USER_AGENT = "KanjiAI curriculum importer/1.0"

# (Japanese chapter label, Vietnamese chapter title, lesson titles)
OUTLINE = [
    ("じこしょうかい", "Tự giới thiệu", ["Là", "Xin chào", "Gia đình", "Bao nhiêu người", "Đến từ"]),
    ("べんきょう", "Học tập", ["Trường học", "Số đếm", "Thứ (trong tuần)", "Từ ngữ", "Học tập"]),
    ("しごと", "Công việc", ["Làm việc, lao động", "Công việc", "Đây là cái gì?", "Có bao nhiêu cái?", "Thời gian"]),
    ("ともだち", "Bạn bè", ["Người như thế nào?", "Mặc áo", "Mặc váy", "Chơi", "Phố xá, thị trấn"]),
    ("きょうのごはん", "Cơm hôm nay", ["Sáng, tối", "Ăn, uống", "Món ăn", "Nhà hàng", "Như thế nào?"]),
    ("しゅみ", "Sở thích", ["Sở thích", "Âm nhạc", "Thể thao", "Thời tiết", "Mùa"]),
    ("かいもの", "Mua sắm", ["Mua sắm", "Cửa hàng, của tiệm", "Máy rút tiền tự động", "Gửi", "Quà tặng"]),
    ("やすみのひ", "Ngày nghỉ", ["Phương tiện giao thông", "Khoảng bao lâu?", "Đường đi", "Ở đâu", "Ra ngoài"]),
    ("すむ", "Sống", ["Nhà", "Tầng 2 chung cư", "Chuyển nhà", "Nhà của giáo viên", "Điện"]),
    ("けんこう", "Sức khỏe", ["Bệnh", "(Bạn) khỏe không?", "Vật - việc quan trọng", "Tương lai", "Hãy nhớ cả những từ này!"]),
]


class VocabularyTableParser(HTMLParser):
    """Extract the source's word, reading, gloss, first example and audio URL."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.current = None
        self.rows = []
        self.capture = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "tbody":
            self.in_body = True
        elif tag == "tr" and self.in_body:
            self.current = {"word": "", "reading": "", "meaning": "", "example_japanese": "", "example_meaning": "", "audio_url": ""}
        if not self.current:
            return
        element_id = attributes.get("id", "")
        classes = attributes.get("class", "")
        if tag == "button" and "playWordSound" in classes:
            self.current["audio_url"] = attributes.get("value", "")
        elif tag == "small" and element_id.startswith("word"):
            self.capture = "word"; self.parts = []
        elif tag == "small" and element_id.startswith("furigana"):
            self.capture = "reading"; self.parts = []
        elif tag == "span" and element_id.startswith("meaning"):
            self.capture = "meaning"; self.parts = []
        elif tag == "p" and not self.current["example_japanese"]:
            self.capture = "example_japanese"; self.parts = []
        elif tag == "span" and "ml-3" in classes and self.current["example_japanese"] and not self.current["example_meaning"]:
            self.capture = "example_meaning"; self.parts = []

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_body = False
        if self.current and self.capture and tag in {"small", "span", "p"}:
            self.current[self.capture] = "".join(self.parts).strip()
            self.capture = None
            self.parts = []
        if tag == "tr" and self.current:
            if self.current["word"] and self.current["meaning"]:
                self.rows.append(self.current)
            self.current = None


def fetch_lesson(chapter, section):
    url = f"{SOURCE_ROOT}/chapter-{chapter}/section-{section}"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        document = response.read().decode("utf-8")
    parser = VocabularyTableParser()
    parser.feed(document)
    if not parser.rows:
        raise RuntimeError(f"Không đọc được dữ liệu từ {url}")
    return chapter, section, parser.rows


def collect_source():
    requests = [(chapter, section) for chapter in range(1, 11) for section in range(1, 6)]
    collected = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(fetch_lesson, chapter, section) for chapter, section in requests]
        for future in as_completed(futures):
            chapter, section, rows = future.result()
            collected[(chapter, section)] = rows
            print(f"Đã đọc chương {chapter}, bài {section}: {len(rows)} từ")
    return collected


def replace_n5(source_rows):
    initialize_database()
    with connect() as db:
        # This is an intentional curriculum replacement requested by the user.
        db.execute("DELETE FROM vocabulary WHERE level='N5'")
        db.execute("DELETE FROM vocabulary_staging WHERE level='N5'")
        db.execute("DELETE FROM lessons WHERE level='N5'")
        db.execute("DELETE FROM lesson_groups WHERE level='N5'")

        total = 0
        for chapter, (japanese_title, group_title, lesson_titles) in enumerate(OUTLINE, start=1):
            db.execute(
                "INSERT INTO lesson_groups(level,japanese_title,title,description,order_index) VALUES ('N5', ?, ?, ?, ?)",
                (japanese_title, group_title, f"Chương {chapter} theo lộ trình JTest.", chapter),
            )
            group_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            for section, lesson_title in enumerate(lesson_titles, start=1):
                order_index = (chapter - 1) * 5 + section
                db.execute(
                    "INSERT INTO lessons(level,title,description,order_index,group_id) VALUES ('N5', ?, ?, ?, ?)",
                    (lesson_title, f"Chương {chapter} · Bài {section} · nguồn JTest", order_index, group_id),
                )
                lesson_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                for entry in source_rows[(chapter, section)]:
                    reading = entry["reading"] or entry["word"]
                    db.execute(
                        """INSERT INTO vocabulary
                           (lesson_id, word, reading, meaning, level, example_japanese, example_reading, example_meaning, audio_url)
                           VALUES (?, ?, ?, ?, 'N5', ?, '', ?, ?)""",
                        (lesson_id, entry["word"], reading, entry["meaning"], entry["example_japanese"], entry["example_meaning"], entry["audio_url"]),
                    )
                    total += 1
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n5_curriculum_source','jtest')")
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n5_curriculum_url', ?)", (SOURCE_ROOT,))
    return total


if __name__ == "__main__":
    rows = collect_source()
    print(f"Hoàn tất: đã nhập {replace_n5(rows)} từ vựng N5 từ JTest.")
