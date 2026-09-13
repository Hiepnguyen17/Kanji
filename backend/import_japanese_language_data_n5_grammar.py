"""Import the full curated N5 grammar set into KanjiAI.

Input is grammar-curated/n5.json from Japanese Language Data (CC BY-SA 4.0).
The import keeps its English source descriptions; KanjiAI's lesson titles are
Vietnamese and follow a beginner, Minna-style lesson progression.
"""
import argparse
import json
import sqlite3
from pathlib import Path

from database import DB_PATH

LESSONS = [
    "Chào hỏi và giới thiệu", "Đồ vật này, kia", "Địa điểm", "Thời gian", "Di chuyển",
    "Hành động lịch sự", "Cùng ai và liệt kê", "Tính từ い", "Tính từ な", "Người và vật ở đâu",
    "Đếm đồ vật và người", "Giờ giấc và khoảng thời gian", "Số tiền và đơn vị", "Từ để hỏi",
    "Mong muốn", "So sánh", "Thể て", "Mời, nhờ và cấm", "Trạng thái tiếp diễn", "Thể ない",
    "Thể た và vừa mới", "Thể thông thường", "Khi và nguyên nhân", "Cụm chỉ vị trí", "Nối tính từ",
]

GROUPS = {
    1: {"desu-polite-copula", "deshita-past-polite-copula", "dewa-arimasen-negative-polite-copula", "particle-wa-topic", "particle-ka-question", "particle-mo-also", "particle-ne-seeking-agreement", "particle-yo-emphasis"},
    2: {"kore-sore-are-demonstratives", "kono-sono-ano-dono-attributive", "particle-no-possession"},
    3: {"koko-soko-asoko-doko"},
    4: {"toki-ni-when-basic", "mai-every-prefix"},
    5: {"particle-e-direction", "particle-ni-target", "particle-kara-from", "particle-made-until"},
    6: {"masu-polite-verb", "mashita-polite-past-verb", "masen-polite-negative-verb", "masendeshita-polite-past-negative-verb", "particle-o-object", "particle-de-means"},
    7: {"particle-to-and-with", "particle-ya-non-exhaustive", "to-exhaustive-listing", "mo-mo-both", "issho-ni-together"},
    8: {"i-adjective-nonpast", "i-adjective-negative", "i-adjective-past", "i-adj-desu-politeness", "i-adj-adverbial-ku"},
    9: {"na-adjective-nonpast", "na-adjective-attributive", "na-adjective-negative", "na-adjective-past", "na-adj-adverbial-ni"},
    10: {"arimasu-existence-inanimate", "imasu-existence-animate", "particle-ga-subject"},
    11: {"counter-tsu", "counter-people-nin", "ikutsu-how-many", "dake-only-basic"},
    12: {"counter-ji-oclock", "counter-fun-minute", "jikan-time-duration", "nanji-what-time", "nanyoubi-day-of-week"},
    13: {"counter-en-money", "counter-hon-long", "counter-mai-flat", "counter-sai-age", "ikura-how-much"},
    14: {"question-words-basic"},
    15: {"tai-desire", "ga-hoshii-wanting-thing"},
    16: {"hou-ga-comparative", "ichiban-superlative"},
    17: {"te-form-basic"},
    18: {"te-kudasai-request", "nai-de-kudasai", "mashou-volitional", "mashou-ka-invitation", "masenka-invitation"},
    19: {"te-imasu-progressive"},
    20: {"nai-form"},
    21: {"ta-form", "mou-ta-already", "mada-not-yet"},
    22: {"da-plain-copula"},
    23: {"kara-cause"},
    24: {"location-nouns-ue-shita"},
    25: {"i-adj-te-joining-kute", "na-adj-te-joining-de"},
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    mapped_ids = set().union(*GROUPS.values())
    missing = {entry["id"] for entry in entries} - mapped_ids
    if missing:
        raise ValueError(f"Unmapped N5 patterns: {sorted(missing)}")
    if len(entries) != len(mapped_ids):
        raise ValueError("A source pattern was assigned more than once or source changed.")
    lesson_for_id = {pattern_id: order for order, ids in GROUPS.items() for pattern_id in ids}
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM grammar_lessons WHERE level='N5'")
        for order, title in enumerate(LESSONS, start=1):
            db.execute("INSERT INTO grammar_lessons(level,title,description,order_index) VALUES ('N5',?,?,?)", (title, f"Bài {order}: {title}.", order))
        lessons = {row[1]: row[0] for row in db.execute("SELECT id, order_index FROM grammar_lessons WHERE level='N5'")}
        for entry in entries:
            order = lesson_for_id[entry["id"]]
            formation = entry.get("formation", "")
            notes = " ".join(entry.get("formation_notes", []))
            note = f"{formation} {notes} [Nguồn: Japanese Language Data; trạng thái: {entry.get('review_status', 'draft')}]".strip()
            cursor = db.execute("INSERT INTO grammar_patterns(lesson_id,formula,explanation_vi,note) VALUES (?,?,?,?)", (lessons[order], entry["pattern"], entry["meaning_en"], note))
            pattern_id = cursor.lastrowid
            for example in entry.get("examples", []):
                db.execute("INSERT INTO grammar_examples(pattern_id,japanese,reading,meaning_vi) VALUES (?,?,?,?)", (pattern_id, example["japanese"], "", example["english"]))
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('grammar_seed_version','n5-full-japanese-language-data-v1')")
    print(f"Imported {len(entries)} N5 patterns into {len(LESSONS)} lessons.")

if __name__ == "__main__":
    main()
