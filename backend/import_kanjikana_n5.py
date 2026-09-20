"""Import the 80-kanji N5 inventory used by Kanjikana into KanjiAI.

The N5 membership and display order follow Kanjikana's Vietnamese N5 pages.
Readings and stroke counts come from KANJIDIC2 (EDRDG); Vietnamese glosses
and Sino-Vietnamese readings are curated locally so the app has no runtime
dependency on the reference website.
"""
from __future__ import annotations

import argparse
import gzip
import io
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from database import DB_PATH, initialize_database
from n5_kanjikana_related import RELATED_WORDS as N5_KANJI_RELATED_WORDS


KANJIDIC2_URL = "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz"

# Character, short Vietnamese meaning, Sino-Vietnamese reading.  Order matches
# https://kanjikana.com/vi/kanji/jlpt/n5 (two pages, frequency order).
KANJIKANA_N5 = [
    ("人", "người", "NHÂN"), ("大", "lớn", "ĐẠI"), ("一", "một", "NHẤT"),
    ("分", "phần, phút", "PHÂN"), ("見", "xem, nhìn", "KIẾN"), ("出", "ra, xuất hiện", "XUẤT"),
    ("日", "ngày, mặt trời", "NHẬT"), ("行", "đi, thực hiện", "HÀNH"), ("前", "phía trước", "TIỀN"),
    ("時", "thời gian, giờ", "THỜI"), ("生", "sống, sinh", "SINH"), ("本", "sách, gốc", "BẢN"),
    ("中", "trong, giữa", "TRUNG"), ("今", "bây giờ", "KIM"), ("間", "khoảng, thời gian", "GIAN"),
    ("年", "năm", "NIÊN"), ("子", "trẻ em, con", "TỬ"), ("長", "dài, trưởng", "TRƯỜNG"),
    ("上", "trên, lên", "THƯỢNG"), ("入", "vào", "NHẬP"), ("後", "sau, phía sau", "HẬU"),
    ("気", "khí, tinh thần", "KHÍ"), ("来", "đến", "LAI"), ("話", "nói, câu chuyện", "THOẠI"),
    ("女", "phụ nữ", "NỮ"), ("国", "quốc gia", "QUỐC"), ("金", "vàng, tiền", "KIM"),
    ("高", "cao", "CAO"), ("下", "dưới, xuống", "HẠ"), ("学", "học", "HỌC"),
    ("先", "trước, tiên", "TIÊN"), ("外", "bên ngoài", "NGOẠI"), ("何", "gì", "HÀ"),
    ("男", "nam giới", "NAM"), ("名", "tên", "DANH"), ("月", "tháng, mặt trăng", "NGUYỆT"),
    ("小", "nhỏ", "TIỂU"), ("聞", "nghe, hỏi", "VĂN"), ("食", "ăn, thức ăn", "THỰC"),
    ("書", "viết, sách", "THƯ"), ("山", "núi", "SƠN"), ("電", "điện", "ĐIỆN"),
    ("二", "hai", "NHỊ"), ("車", "xe", "XA"), ("水", "nước", "THỦY"),
    ("木", "cây, gỗ", "MỘC"), ("母", "mẹ", "MẪU"), ("校", "trường học", "HIỆU"),
    ("父", "cha", "PHỤ"), ("白", "trắng", "BẠCH"), ("語", "từ, ngôn ngữ", "NGỮ"),
    ("十", "mười", "THẬP"), ("万", "mười nghìn", "VẠN"), ("友", "bạn", "HỮU"),
    ("川", "sông", "XUYÊN"), ("三", "ba", "TAM"), ("天", "trời", "THIÊN"),
    ("東", "đông", "ĐÔNG"), ("半", "một nửa", "BÁN"), ("北", "bắc", "BẮC"),
    ("火", "lửa", "HỎA"), ("土", "đất", "THỔ"), ("南", "nam", "NAM"),
    ("千", "nghìn", "THIÊN"), ("西", "tây", "TÂY"), ("毎", "mỗi", "MỖI"),
    ("休", "nghỉ ngơi", "HƯU"), ("八", "tám", "BÁT"), ("読", "đọc", "ĐỘC"),
    ("五", "năm", "NGŨ"), ("四", "bốn", "TỨ"), ("百", "trăm", "BÁCH"),
    ("円", "hình tròn, yên", "VIÊN"), ("午", "buổi trưa", "NGỌ"), ("七", "bảy", "THẤT"),
    ("左", "bên trái", "TẢ"), ("右", "bên phải", "HỮU"), ("雨", "mưa", "VŨ"),
    ("六", "sáu", "LỤC"), ("九", "chín", "CỬU"),
]

# Bộ thủ chính để hiển thị trong trang tra cứu.  KANJIDIC2 có số hiệu bộ thủ
# nhưng không cung cấp luôn chữ bộ thủ; giữ bảng này cạnh danh sách N5 giúp dữ
# liệu hiển thị nhất quán và không phụ thuộc vào một website bên ngoài.
N5_RADICALS = {
    "人": "人", "大": "大", "一": "一", "分": "刀", "見": "見", "出": "凵",
    "日": "日", "行": "行", "前": "刀", "時": "日", "生": "生", "本": "木",
    "中": "丨", "今": "人", "間": "門", "年": "干", "子": "子", "長": "長",
    "上": "一", "入": "入", "後": "彳", "気": "气", "来": "木", "話": "言",
    "女": "女", "国": "囗", "金": "金", "高": "高", "下": "一", "学": "子",
    "先": "儿", "外": "夕", "何": "人", "男": "田", "名": "口", "月": "月",
    "小": "小", "聞": "耳", "食": "食", "書": "曰", "山": "山", "電": "雨",
    "二": "二", "車": "車", "水": "水", "木": "木", "母": "母", "校": "木",
    "父": "父", "白": "白", "語": "言", "十": "十", "万": "一", "友": "又",
    "川": "川", "三": "一", "天": "大", "東": "木", "半": "十", "北": "匕",
    "火": "火", "土": "土", "南": "十", "千": "十", "西": "襾", "毎": "毋",
    "休": "人", "八": "八", "読": "言", "五": "二", "四": "囗", "百": "白",
    "円": "冂", "午": "十", "七": "一", "左": "工", "右": "口", "雨": "雨",
    "六": "八", "九": "乙",
}


def load_kanjidic2(path: Path | None) -> ET.Element:
    if path:
        raw = path.read_bytes()
    else:
        request = urllib.request.Request(KANJIDIC2_URL, headers={"User-Agent": "KanjiAI data importer"})
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return ET.parse(io.BytesIO(raw)).getroot()


def dictionary_rows(root: ET.Element) -> dict[str, tuple[str, str, int]]:
    wanted = {character for character, _, _ in KANJIKANA_N5}
    rows: dict[str, tuple[str, str, int]] = {}
    for entry in root.findall("character"):
        character = entry.findtext("literal", "")
        if character not in wanted:
            continue
        strokes = int(entry.findtext("misc/stroke_count", "0"))
        readings = entry.findall("reading_meaning/rmgroup/reading")
        on = [item.text or "" for item in readings if item.get("r_type") == "ja_on"]
        kun = [item.text or "" for item in readings if item.get("r_type") == "ja_kun"]
        rows[character] = ("・".join(on), "・".join(kun), strokes)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kanjidic2", type=Path, help="Optional local kanjidic2.xml or .xml.gz")
    args = parser.parse_args()
    initialize_database()
    details = dictionary_rows(load_kanjidic2(args.kanjidic2))
    missing = [character for character, _, _ in KANJIKANA_N5 if character not in details]
    if missing:
        raise ValueError("KANJIDIC2 thiếu các chữ: " + " ".join(missing))

    with sqlite3.connect(DB_PATH) as db:
        characters = [character for character, _, _ in KANJIKANA_N5]
        placeholders = ",".join("?" for _ in characters)
        db.execute(f"DELETE FROM kanji WHERE level='N5' AND char NOT IN ({placeholders})", characters)
        for order, (character, meaning, han_viet) in enumerate(KANJIKANA_N5, 1):
            on, kun, strokes = details[character]
            db.execute(
                """INSERT INTO kanji(char,meaning,on_reading,kun_reading,strokes,level,radical,han_viet,order_index)
                   VALUES (?, ?, ?, ?, ?, 'N5', ?, ?, ?)
                   ON CONFLICT(char) DO UPDATE SET meaning=excluded.meaning,
                     on_reading=excluded.on_reading, kun_reading=excluded.kun_reading,
                     strokes=excluded.strokes, level='N5', radical=excluded.radical, han_viet=excluded.han_viet,
                     order_index=excluded.order_index""",
                (character, meaning, on, kun, strokes, N5_RADICALS[character], han_viet, order),
            )
        db.execute("DELETE FROM kanji_related_words WHERE kanji IN (SELECT char FROM kanji WHERE level='N5')")
        for character, words in N5_KANJI_RELATED_WORDS.items():
            for related_order, (word, reading, meaning) in enumerate(words, 1):
                db.execute("""INSERT INTO kanji_related_words(kanji,word,reading,meaning,order_index)
                    VALUES (?, ?, ?, ?, ?)""", (character, word, reading, meaning, related_order))
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n5_kanji_source','kanjikana-order-kanjidic2-v1')")
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n5_kanji_related_words_version','kanjikana-n5-common-words-vi-v1')")
    print(f"Imported {len(KANJIKANA_N5)} N5 kanji in Kanjikana frequency order.")


if __name__ == "__main__":
    main()
