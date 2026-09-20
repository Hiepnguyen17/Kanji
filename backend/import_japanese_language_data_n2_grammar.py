"""Import the complete N2 inventory into a 26-lesson Vietnamese course.

Source patterns and Japanese examples: Japanese Language Data (CC BY-SA 4.0).
Vietnamese meanings/examples live in ``n2_vi.json`` so they can be reviewed
without touching the importer.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

from database import DB_PATH
from n2_meanings_vi import MEANINGS

LESSONS = [
    ("Thời điểm · Ngay sau khi", "Những mẫu xác định thời điểm và sự việc xảy ra ngay sau một mốc."),
    ("Đang diễn ra · Tiến hành", "Diễn tả quá trình đang tiếp diễn hoặc biến đổi theo thời gian."),
    ("Sau khi · Tiếp theo", "Nói kết quả hoặc hành động tiếp nối sau một quá trình."),
    ("Phạm vi · Bắt đầu và kết thúc", "Xác định phạm vi, mốc bắt đầu, điểm kết thúc và quá trình đi qua."),
    ("Chỉ · Giới hạn", "Giới hạn đối tượng, mức độ hoặc phạm vi của nhận định."),
    ("Không chỉ · Thêm vào đó", "Bổ sung thông tin và nhấn rằng phạm vi không dừng ở một yếu tố."),
    ("Về · Đối với", "Nêu chủ đề, đối tượng hoặc lập trường được nói tới."),
    ("Dựa trên · Tiêu chuẩn", "Nêu căn cứ, tiêu chuẩn và dữ liệu dùng để đánh giá."),
    ("Liên quan · Tương ứng", "Nói quan hệ, sự tương ứng hoặc thay đổi đi kèm."),
    ("Liệt kê · Ví dụ", "Liệt kê nhiều yếu tố hoặc đưa ví dụ đại diện."),
    ("Bất kể · Bất chấp", "Diễn tả kết quả không thay đổi dù điều kiện khác nhau."),
    ("Phủ định mạnh", "Khẳng định mạnh điều không thể, không xảy ra hoặc không được chấp nhận."),
    ("Về chủ đề", "Định nghĩa, diễn giải và nêu bản chất của một vấn đề."),
    ("Mặc dù · Tuy nhiên", "Nối hai ý tương phản hoặc trái với điều thường được mong đợi."),
    ("Giả định · Dù cho", "Đặt điều kiện giả định, nhượng bộ hoặc trường hợp có thể xảy ra."),
    ("Nguyên nhân · Lý do 1", "Nêu nguyên nhân trực tiếp, căn cứ hoặc lý do trang trọng."),
    ("Nguyên nhân · Lý do 2", "Giải thích nguyên nhân kèm thái độ, trách nhiệm hoặc kết luận."),
    ("Không thể · Khó khăn", "Nói điều khó làm, không thể làm hoặc có nguy cơ xảy ra."),
    ("Đánh giá · Nhận xét", "Đưa nhận xét dựa trên góc nhìn, mức độ hoặc tiêu chuẩn."),
    ("Kết quả", "Nêu kết quả cuối cùng, kết luận hoặc điều đạt tới."),
    ("Nhấn mạnh · Nói nhẹ", "Điều chỉnh mức độ nhấn mạnh hoặc làm mềm nhận định."),
    ("Suy đoán · Đoán định", "Nói điều được suy ra từ dấu hiệu hoặc giả thiết."),
    ("Cảm tưởng · Chủ trương", "Nêu cảm tưởng, cách nhìn hoặc lập trường của người nói."),
    ("Đề xuất · Ý chí", "Nói quyết tâm, phương châm, lời đề xuất và hành động có chủ ý."),
    ("Cảm xúc mạnh", "Diễn tả cảm xúc đạt mức cao hoặc không thể kìm nén."),
    ("Mong ước · Cảm động", "Nói mong ước, sự cảm động và đánh giá giàu cảm xúc."),
]

# Rules are ordered.  They group by learning function; any new upstream item
# that matches no rule is placed in the currently smallest lesson, making the
# source change visible in validation instead of silently dropping it.
RULES = [
    (1, r"ya-inaya|ka-nai-ka|nari-as-soon|ga-hayai|ka-to-omou-to|ni-atatte|sai-ni"),
    (2, r"tsutsu-aru|tsutsu-while|bakari-no|makuru-extensively|ni-shitagatte"),
    (3, r"sue-ni|ageku|hate-ni|wo-hete|te-kara-to-iu|sobakara|ato-wa"),
    (4, r"ni-wataru|ni-itaru-made|wo-tsuujite|wo-chuushin|ni-sakidatte|ni-kakete"),
    (5, r"ni-kagitte|ni-kagirazu|dake-nara|ni-suginai|hodo-dewa-nai|made-mo-nai|nai-made-mo"),
    (6, r"wa-mochiron|no-minarazu|nai-nomi-narazu|ue-ni|shikamo|wa-oroka"),
    (7, r"ni-shite-mireba|kara-iu-to|kara-miru-to|kara-suru-to|toshite|mono-to-shite"),
    (8, r"wo-fumaete|wo-motoni|ni-terashite|ni-kangamite|doori|no-moto-de"),
    (9, r"ni-oujite|ni-kotaete|ni-kakatte|ni-tomonatte|ni-sotte"),
    (10, r"yara-yara|dano-dano|to-itta|nari-tomo|to-iu-ka"),
    (11, r"ni-kakawarazu|wo-towazu|wa-tomokaku|wa-sate-oki|wo-yoso-ni"),
    (12, r"mai-not|yashinai|sou-ni-nai|zu-jimai|zaru-wo-enai|te-wa-irarenai"),
    (13, r"to-iu-mono|to-iu-koto|to-iu-no-wa|to-miru-see|mono-ga-aru"),
    (14, r"ni-mo-kakawarazu|to-wa-ie|to-wa-iu|mono-no|hanmen|you-de-seemingly"),
    (15, r"ni-shiro|toshite-mo|you-to-regardless|you-to-mai|to-sureba|you-nara|mono-nara|tatte-even|to-areba|sae-sureba"),
    (16, r"ni-tsuki|yue-ni|koto-kara|amari-too|ba-koso|kara-koso|kara-ni-wa"),
    (17, r"mono-dakara|koto-tote|kara-to-itte|koto-dakara|atte-no|to-atte|datte-casual"),
    (18, r"kane-nai|kane-ru|dzurai|gatai|nuku|uru-possible|sobireru|osore-ga-aru"),
    (19, r"ni-shite-wa|kara-shite|kiwamari|kagiri-da|hodo-no-mono|ni-terashite"),
    (20, r"ni-itaru$|kekka-result|shidai-de|to-iu-koto-wa"),
    (21, r"koso|dake-mashi|naku-mo-nai|te-mo-ii-kurai|to-itte-without"),
    (22, r"to-mieru|you-de|to-sureba|ka-to-iu-to|to-miru"),
    (23, r"to-iu-mono-da|to-iu-koto-da|to-iu-no-wa|mono-ga-aru|to-iu-ka"),
    (24, r"beku|te-shikaru|ue-wa|ijou-since|ni-shiro|mai-not-likely"),
    (25, r"wo-komete|te-yamanai|kagiri-da-emotional|zu-ni-wa-irarenai|nai-dewa-irarenai"),
    (26, r"mono-ga-aru|kagiri-da-emotional|kiwamari-nai|to-bakari-ni|meku-have-look"),
]


def lesson_map(entries: list[dict]) -> dict[str, int]:
    result: dict[str, int] = {}
    counts = {number: 0 for number in range(1, 27)}
    for entry in entries:
        identifier = entry["id"]
        for number, pattern in RULES:
            if re.search(pattern, identifier):
                result[identifier] = number
                counts[number] += 1
                break
        else:
            number = min(counts, key=lambda item: (counts[item], item))
            result[identifier] = number
            counts[number] += 1
    return result


def vi_formula(value: str) -> str:
    replacements = [
        ("Plain form", "TTT"), ("V plain non-past", "V thể từ điển"),
        ("V plain", "V thể từ điển"), ("Verb dict-form", "V thể từ điển"),
        ("Verb dict", "V thể từ điển"), ("Verb ます-stem", "Vます"),
        ("Verb-た form", "Vた"), ("V-た form", "Vた"),
        ("Verb-て form", "Vて"), ("V-て form", "Vて"),
        ("V ない-form", "Vない"), ("V negative stem", "gốc Vない"),
        ("Verb", "V"), ("Noun", "N"), ("noun", "N"),
        ("Number", "Số"), ("counter", "lượng từ"),
        ("i-adj", "Aい"), ("na-adj", "Aな"), ("form", "thể"),
    ]
    for old, new in replacements:
        value = value.replace(old, new)
    value = value.replace("plain thể", "TTT").replace("plain", "TTT")
    value = value.replace("V khả năng thể", "V thể khả năng")
    value = value.replace("V dict-thể", "V thể từ điển").replace("V dict", "V thể từ điển")
    value = value.replace("V ます-gốc", "Vます").replace("ます-gốc", "Vます")
    value = value.replace("V ば-thể", "Vば").replace("Aい gốc", "gốc Aい").replace("Aな gốc", "gốc Aな")
    value = value.replace("V ない-gốc", "gốc Vない").replace("V phủ định gốc", "gốc Vない")
    words = {
        "stem": "gốc", "root": "gốc", "negative": "phủ định",
        "potential": "khả năng", "conditional": "điều kiện",
        "volitional": "ý chí", "sentence-initial": "đầu câu",
        "mid-sentence": "giữa câu", "sentence-final": "cuối câu",
        "casual": "thân mật", "formal": "trang trọng", "phrase": "cụm từ",
        "group": "nhóm", "category": "loại", "emotion": "cảm xúc",
        "sentence": "S", "adj": "A",
        "or": "hoặc", "and": "và", "vs": "so với",
    }
    for old, new in words.items():
        value = re.sub(rf"\b{re.escape(old)}\b", new, value, flags=re.I)
    return value


# N2 is normalized separately because the N1 importer still imports the older
# generic formatter above.  This keeps an N2 data refresh from silently
# changing the already-reviewed N1 formulas.
N2_FORMULA_OVERRIDES = {
    "amari-too-much": "V (TTT) / Aい / Aな + な / N + の + あまり",
    "sobakara": "V (TTT) / Vた + そばから",
    "ka-nai-ka-no-uchi-ni": "Vる + か + Vない + かのうちに",
    "nai-nomi-narazu": "Vない + のみならず",
    "yara-yara": "N1 + やら + N2 + やら",
    "dano-dano": "TTT + だの + TTT + だの",
    "to-iu-ka": "TTT + というか + TTT",
    "atte-no-thanks-to": "N1 + あっての + N2",
    "zu-ni-wa-irarenai": "Vない (bỏ ない) + ずにはいられない",
    "zu-jimai": "Vない (bỏ ない) + ずじまい",
    "zutomo-even-without": "Vない (bỏ ない) + ずとも",
    "zaru-wo-enai": "Vない (bỏ ない) + ざるを得ない",
    "naku-mo-nai": "Vない (bỏ い) + くもない / もない",
    "you-to-regardless": "V (thể ý chí) + と / ようと",
    "you-to-mai-to": "V (thể ý chí) + と + Vる / Gốc Vます + まい（と）",
    "mai-not-likely": "Vる / Gốc Vます + まい",
    "mono-nara-if-possible": "V (thể khả năng) + ものなら",
    "ba-koso-precisely-because": "V (thể ば) + こそ",
    "sae-sureba-if-only": "Gốc Vます / N + さえ + thể điều kiện",
    "buru-pretend": "N / Aい (bỏ い) / Aな + ぶる",
    "kiwamari-nai": "Aな + 極まりない / 極まる",
}


def vi_formula_n2(identifier: str, value: str) -> str:
    """Convert an N2 source formula into learner-facing Vietnamese notation."""
    if identifier in N2_FORMULA_OVERRIDES:
        return N2_FORMULA_OVERRIDES[identifier]

    replacements = [
        ("V plain non-past", "Vる"),
        ("Verb plain", "V (TTT)"),
        ("Verb dict-form", "Vる"),
        ("Verb dict", "Vる"),
        ("V dict-form", "Vる"),
        ("V dict", "Vる"),
        ("Verb ます-stem", "Gốc Vます"),
        ("V ます-stem", "Gốc Vます"),
        ("Verb-た form", "Vた"),
        ("V-た form", "Vた"),
        ("Verb-て form", "Vて"),
        ("V-て form", "Vて"),
        ("V ない-form", "Vない"),
        ("V ない", "Vない"),
        ("V negative stem", "Vない (bỏ ない)"),
        ("Verb volitional", "V (thể ý chí)"),
        ("V volitional", "V (thể ý chí)"),
        ("V potential form", "V (thể khả năng)"),
        ("V ば-form", "V (thể ば)"),
        ("V plain", "V (TTT)"),
        ("Plain form", "TTT"),
        ("Noun", "N"),
        ("noun", "N"),
        ("i-adj stem", "Aい (bỏ い)"),
        ("na-adj root", "Aな"),
        ("i-adj", "Aい"),
        ("na-adj", "Aな"),
        ("sentence-initial", "đầu câu"),
        ("phrase", "cụm từ"),
        ("conditional", "thể điều kiện"),
        ("casual", "thân mật"),
    ]
    for old, new in replacements:
        value = value.replace(old, new)

    # Guard against upstream spelling variants without turning explanation
    # words into grammar chips.
    value = re.sub(r"\bV\s+plain\b", "V (TTT)", value, flags=re.I)
    value = re.sub(r"\bplain form\b", "TTT", value, flags=re.I)
    value = re.sub(r"\bverb\b", "V", value, flags=re.I)
    value = re.sub(r"\bnumber\b", "Số", value, flags=re.I)
    value = re.sub(r"\bcounter\b", "lượng từ", value, flags=re.I)
    value = re.sub(r"\bor\b", "hoặc", value, flags=re.I)
    value = re.sub(r"\band\b", "và", value, flags=re.I)
    value = re.sub(r"\bstem\b", "gốc", value, flags=re.I)
    value = re.sub(r"\broot\b", "gốc", value, flags=re.I)
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--translations", type=Path, default=Path(__file__).with_name("n2_vi.json"))
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    translations = json.loads(args.translations.read_text(encoding="utf-8"))
    source_ids = {entry["id"] for entry in entries}
    if source_ids != set(translations):
        raise ValueError("Bản dịch N2 không khớp inventory nguồn.")
    if source_ids != set(MEANINGS):
        raise ValueError("Bảng nghĩa N2 đã biên tập không khớp inventory nguồn.")
    mapping = lesson_map(entries)
    if set(mapping) != source_ids or len(mapping) != len(entries):
        raise ValueError("Có mẫu N2 bị thiếu hoặc phân trùng bài.")

    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM grammar_lessons WHERE level='N2'")
        for order, (title, description) in enumerate(LESSONS, 1):
            db.execute("INSERT INTO grammar_lessons(level,title,description,order_index) VALUES ('N2',?,?,?)", (title, description, order))
        lesson_ids = {order: identifier for identifier, order in db.execute("SELECT id,order_index FROM grammar_lessons WHERE level='N2'")}
        for entry in entries:
            translated = translations[entry["id"]]
            meaning = MEANINGS[entry["id"]].strip()
            example_vi = translated["example"].strip()
            if not meaning or not example_vi:
                raise ValueError(f"Thiếu nội dung Việt cho {entry['id']}")
            cursor = db.execute(
                "INSERT INTO grammar_patterns(lesson_id,formula,explanation_vi,note) VALUES (?,?,?,?)",
                (lesson_ids[mapping[entry["id"]]], vi_formula_n2(entry["id"], entry["pattern"]), meaning,
                 f"Mẫu này thường dùng với nghĩa “{meaning}”. Chú ý văn phong và sắc thái của câu ví dụ."),
            )
            example = (entry.get("examples") or [None])[0]
            if example:
                db.execute("INSERT INTO grammar_examples(pattern_id,japanese,reading,meaning_vi) VALUES (?,?,?,?)", (cursor.lastrowid, example["japanese"], "", example_vi))
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n2_grammar_seed_version','n2-full-japanese-language-data-vi-v1')")
    print(f"Imported {len(entries)} N2 patterns into {len(LESSONS)} lessons.")


if __name__ == "__main__":
    main()
