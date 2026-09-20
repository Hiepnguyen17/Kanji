"""Import all Japanese Language Data N1 patterns into KanjiAI's 20-topic path."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

from database import DB_PATH
from n1_meanings_vi import MEANINGS


LESSONS = [
    ("Quan hệ thời gian", "Các mẫu diễn tả thời điểm, trước sau và khoảnh khắc chuyển biến."),
    ("Phạm vi bắt đầu · Giới hạn", "Xác định điểm bắt đầu, điểm kết thúc và phạm vi áp dụng."),
    ("Giới hạn · Bổ sung", "Giới hạn đối tượng hoặc bổ sung yếu tố được nhấn mạnh."),
    ("Ví dụ minh họa", "Nêu ví dụ, phép ví von và đối tượng đại diện."),
    ("Liên quan · Không liên quan", "Diễn tả quan hệ, sự liên đới hoặc thái độ không màng đến."),
    ("Trạng thái · Dáng vẻ", "Miêu tả trạng thái, biểu hiện và dáng vẻ quan sát được."),
    ("Hành động đi kèm", "Kết hợp hai mục đích hoặc những hành động diễn ra song song."),
    ("Nghịch tiếp · Mặc dù", "Nối các ý tương phản, nhượng bộ hoặc trái với dự đoán."),
    ("Nguyên nhân · Lý do", "Nêu nguyên nhân, căn cứ và lý do dẫn tới nhận định."),
    ("Điều kiện", "Đặt điều kiện, giả định và trường hợp có thể xảy ra."),
    ("Mục đích", "Nêu mục tiêu và ý định của hành động trong văn phong trang trọng."),
    ("Có thể · Không thể", "Đánh giá khả năng, tính khả thi và điều khó thực hiện."),
    ("Khuynh hướng", "Nói xu hướng, đặc điểm thường gặp và diễn biến có tính quy luật."),
    ("Mức độ · Bổ sung", "Diễn tả mức độ cao, giới hạn và thông tin bổ sung."),
    ("So sánh đối chiếu", "So sánh, đối chiếu và làm nổi bật sự khác biệt."),
    ("Kết quả cuối cùng", "Nêu kết cục, kết quả tất yếu hoặc điểm cuối của quá trình."),
    ("Nhấn mạnh", "Nhấn mạnh số lượng, mức độ, đối tượng hoặc sự bất ngờ."),
    ("Chủ trương · Đoán định", "Thể hiện lập trường, phán đoán và kết luận của người nói."),
    ("Đánh giá · Cảm tưởng", "Đưa đánh giá về tư cách, giá trị và ấn tượng."),
    ("Tâm tình · Cảm xúc mạnh", "Bộc lộ cảm xúc mạnh, sự tiếc nuối và thái độ của người nói."),
]


RULES = [
    (1, r"ori-ni|hitotabi|ya-literary|nari-as-soon|ga-hayai|wo-mae-ni|n-to-suru|ni-sakigakete|ni-atte$"),
    (2, r"wo-kawakiri|wo-kagiri|to-iwazu|ni-itatte-wa|gurumi|kitte-no"),
    (3, r"narade-wa|wo-oite|nomi-only|desura|tada-de-sae|mo-saru-koto|ni-mo-mashite"),
    (4, r"wo-hikiai|ni-nazoraete|iwaba|gotoku|gotoki"),
    (5, r"ni-matsuwaru|ni-kakawaru|mo-kamawa|wo-shirime|wo-kaerimi|yoshi-mi|ikan-ni-yorazu"),
    (6, r"n-bakari|sanagara|to-oboshii|n-to-bakari|nagara-no|sono-mono|mekasu|to-yara"),
    (7, r"katawara|gatera|katagata|wo-kanete|to-aimatte|nagara-ni"),
    (8, r"de-ari-nagara|nagara-mo|to-iedomo|koso-are|to-wa-urahara|wo-mono-to-mo"),
    (9, r"yue-no|taru-yuen|ni-hoka-naranai|hoka-naranu|made-no-koto|te-mae"),
    (10, r"de-are-de-are|nari-nari|to-nareba|to-naru-to|to-atte-wa|u-mono-nara|de-atta-to-shitemo|aro-u-tomo"),
    (11, r"n-ga-tame|beku-shite|made-da"),
    (12, r"ni-kataku-nai|beku-mo-nai|nai-de-mo-nai|ni-wa-oyoba|ni-tari$|ni-taeru|ni-taenai|you-ni-mo-nai|u-ni-mo"),
    (13, r"ni-ari-gachi|ikkou-ni-nai|beku-shite|koto-nagara"),
    (14, r"ni-mo-hodo|hodo-no|no-ue-nai|no-kiwami|wo-kiwameru|to-itta-tokoro|ni-mo-mashite"),
    (15, r"ni-nottotte|nara-mada-shimo|nara-iza-shirazu|to-iwazu|ni-nazoraete"),
    (16, r"ba-sore-made|ga-sai-go|wo-yogi-naku|zu-ni-wa-sumanai|zu-ni-wa-okanai|nai-dewa-okanai|oose-ru|konasu"),
    (17, r"tari-tomo|tari-mo-shinai|mo-nan-tomo-nai|naku-te-nan-de|koto-mo-arou|aro-u-koto-ka|made-mo-naku"),
    (18, r"ni-soui-nai|to-minasu|to-sareru|mai-ka|to-shita-tokoro|te-shikarubeki|bekarazu"),
    (19, r"tomo-arou|taru-mono|ni-teihyou|ni-tari-nai|iyashiku-mo|tou-no|to-wa$|ni-taeru"),
    (20, r"wo-kinjienai|no-itari|te-yamanai|ikan-se-n|ashikara-zu|manzara|ni-aki-tarazu|mono-wo-if-only"),
]


def lesson_map(entries: list[dict]) -> dict[str, int]:
    result: dict[str, int] = {}
    counts = {number: 0 for number in range(1, len(LESSONS) + 1)}
    for entry in entries:
        for number, pattern in RULES:
            if re.search(pattern, entry["id"]):
                result[entry["id"]] = number
                counts[number] += 1
                break
        else:
            number = min(counts, key=lambda item: (counts[item], item))
            result[entry["id"]] = number
            counts[number] += 1
    return result


N1_FORMULA_OVERRIDES = {
    "tomo-arou": "N1 + ともあろう + N2",
    "nari-nari": "N1 / V1 + なり + N2 / V2 + なり",
    "to-iwazu-to-iwazu": "N1 + といわず + N2 + といわず",
    "de-are-de-are": "N1 + であれ + N2 + であれ",
    "hodo-no": "N1 / TTT + ほどの + N2",
    "yue-no": "N1 + (が)ゆえの / ゆえの + N2",
    "hoka-naranu": "N1 + ほかならぬ + N2",
    "gotoki-like": "N1 + ごとき (+ N2)",
    "zu-ni-wa-okanai": "Vない (bỏ ない) + ずにはおかない",
    "zu-ni-wa-sumanai": "Vない (bỏ ない) + ずにはすまない / Vない + ではすまない",
    "zu-mogana": "Vない (bỏ ない) + ずもがな",
    "n-ga-tame": "Vない (bỏ ない) + んがため(に)",
    "n-bakari": "Vない (bỏ ない) + んばかり(に)",
    "you-ni-mo-nai": "V (thể ý chí) + にも + V (thể khả năng, phủ định)",
    "u-ni-mo": "V (thể ý chí) + にも",
    "u-mono-nara": "V (thể ý chí) + ものなら",
    "n-to-suru": "V (thể ý chí) + んとする",
    "n-to-bakari-ni": "V (thể ý chí) + ん + とばかりに",
    "aro-u-tomo": "V (thể ý chí) + とも / あろうとも",
    "tari-tomo": "Số + lượng từ + たりとも + thể phủ định",
    "to-itta-tokoro-da": "Số / N + といったところだ",
    "ba-sore-made": "V (thể ば) / thể điều kiện + それまでだ",
    "mo-nan-tomo-nai": "Aい (bỏ い) + くもなんともない / Aな + でもなんでもない",
    "naku-te-nan-de-arou": "Aい (bỏ い) + くて / Aな + で + なんであろう",
    "hitotabi": "ひとたび + V + (ば / と / たら)",
    "ikkou-ni-nai": "いっこうに + Vない",
}


def vi_formula_n1(identifier: str, value: str) -> str:
    """Convert an N1 source formula into learner-facing notation."""
    if identifier in N1_FORMULA_OVERRIDES:
        return N1_FORMULA_OVERRIDES[identifier]

    replacements = [
        ("V plain non-past", "Vる"),
        ("Verb plain", "V (TTT)"),
        ("Verb dict-form", "Vる"),
        ("Verb dict", "Vる"),
        ("V dict-form", "Vる"),
        ("V dict", "Vる"),
        ("Verb ます-stem", "Gốc Vます"),
        ("V ます-stem", "Gốc Vます"),
        ("V stem", "Gốc Vます"),
        ("Verb-た form", "Vた"),
        ("V-た form", "Vた"),
        ("V-たら", "V (thể たら)"),
        ("V た", "Vた"),
        ("Verb-て form", "Vて"),
        ("V-て form", "Vて"),
        ("V ない-form", "Vない"),
        ("V negative stem", "Vない (bỏ ない)"),
        ("V ない-stem", "Vない (bỏ ない)"),
        ("Verb volitional", "V (thể ý chí)"),
        ("V volitional", "V (thể ý chí)"),
        ("V potential negative", "V (thể khả năng, phủ định)"),
        ("V ば-form", "V (thể ば)"),
        ("V plain", "V (TTT)"),
        ("Plain form", "TTT"),
        ("Noun", "N"),
        ("noun", "N"),
        ("Number", "Số"),
        ("counter", "lượng từ"),
        ("i-adj", "Aい"),
        ("na-adj", "Aな"),
        ("adj", "A"),
        ("sentence-initial", "đầu câu"),
        ("mid-sentence", "giữa câu"),
        ("sentence-final", "cuối câu"),
        ("negative", "phủ định"),
        ("conditional", "thể điều kiện"),
        ("emotion", "cảm xúc"),
        ("group", "nhóm"),
        ("category", "loại"),
    ]
    for old, new in replacements:
        value = value.replace(old, new)

    value = re.sub(r"\bV\s+plain\b", "V (TTT)", value, flags=re.I)
    value = re.sub(r"\bplain form\b", "TTT", value, flags=re.I)
    value = re.sub(r"\bverb\b", "V", value, flags=re.I)
    value = re.sub(r"\bor\b", "hoặc", value, flags=re.I)
    value = re.sub(r"\band\b", "và", value, flags=re.I)
    value = re.sub(r"\bstem\b", "gốc", value, flags=re.I)
    value = re.sub(r"\broot\b", "gốc", value, flags=re.I)
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--translations", type=Path, default=Path(__file__).with_name("n1_vi.json"))
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    translations = json.loads(args.translations.read_text(encoding="utf-8"))
    source_ids = {entry["id"] for entry in entries}
    if source_ids != set(translations):
        raise ValueError("Bản dịch N1 không khớp inventory nguồn.")
    if source_ids != set(MEANINGS):
        raise ValueError("Bảng nghĩa N1 đã biên tập không khớp inventory nguồn.")
    mapping = lesson_map(entries)
    if set(mapping) != source_ids:
        raise ValueError("Có mẫu N1 chưa được phân bài.")

    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM grammar_lessons WHERE level='N1'")
        for order, (title, description) in enumerate(LESSONS, 1):
            db.execute("INSERT INTO grammar_lessons(level,title,description,order_index) VALUES ('N1',?,?,?)", (title, description, order))
        lesson_ids = {order: identifier for identifier, order in db.execute("SELECT id,order_index FROM grammar_lessons WHERE level='N1'")}
        for entry in entries:
            localized = translations[entry["id"]]
            meaning = MEANINGS[entry["id"]].strip()
            example_vi = localized["example"].strip()
            if not meaning or not example_vi:
                raise ValueError(f"Thiếu nội dung Việt cho {entry['id']}")
            cursor = db.execute(
                "INSERT INTO grammar_patterns(lesson_id,formula,explanation_vi,note) VALUES (?,?,?,?)",
                (lesson_ids[mapping[entry["id"]]], vi_formula_n1(entry["id"], entry["pattern"]), meaning,
                 f"Mẫu N1 trang trọng với nghĩa “{meaning}”. Cần chú ý ngữ cảnh và sắc thái của câu."),
            )
            example = entry["examples"][0]
            db.execute(
                "INSERT INTO grammar_examples(pattern_id,japanese,reading,meaning_vi) VALUES (?,?,?,?)",
                (cursor.lastrowid, example["japanese"], "", example_vi),
            )
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n1_grammar_seed_version','n1-full-japanese-language-data-vi-v1')")
    counts = {number: list(mapping.values()).count(number) for number in range(1, len(LESSONS) + 1)}
    print(f"Imported {len(entries)} N1 patterns into {len(LESSONS)} lessons: {counts}")


if __name__ == "__main__":
    main()
