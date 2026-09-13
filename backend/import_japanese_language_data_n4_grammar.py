"""Import the complete curated JLPT N4 grammar set in Vietnamese.

Source: Japanese Language Data, grammar-curated/n4.json (CC BY-SA 4.0).
The source's English explanations are used as the factual reference; the
learner-facing meanings and notes below are Vietnamese editorial translations.
"""
import argparse
import json
import sqlite3
from pathlib import Path

from database import DB_PATH

LESSONS = [
    "Nhấn mạnh và nhờ vả lịch sự", "Khả năng và giới hạn", "Động từ chỉ lý do",
    "Trạng thái và hoàn thành", "So sánh và kết quả", "Dự định và kế hoạch",
    "Khuyên bảo và phỏng đoán", "Mệnh lệnh và nghĩa vụ", "Theo như và sau khi",
    "Điều kiện ば và なら", "Mục đích và biến đổi", "Bị động", "Nhóm động từ",
    "Nguyên nhân", "Câu hỏi tổng và thử làm", "Kính ngữ cho cấp trên",
    "Vì mục đích và sử dụng vào", "Trông có vẻ và rủi ro", "Quá mức và dễ/khó",
    "Trường hợp và nghịch lý", "Sắp/đang/vừa xong và vừa mới", "Nghe nói và hình như",
    "Sai khiến", "Kính ngữ", "Khiêm nhường ngữ",
]

# Each item is an editorial Vietnamese rendering of the corresponding JLD
# English meaning.  Keep IDs stable so a source update is easy to review.
VI = {
 "potential-form":"có thể làm / có khả năng làm", "passive-form":"bị làm; cũng diễn tả việc bị ảnh hưởng ngoài ý muốn", "causative-form":"bắt hoặc cho phép ai làm", "ta-koto-ga-aru":"đã từng làm (kinh nghiệm)", "tsumori-intention":"dự định / có ý định làm", "to-omou":"tôi nghĩ rằng", "to-iu":"nói rằng; được gọi là", "darou-deshou-conjecture":"chắc là / có lẽ", "kamoshirenai-might":"có thể / biết đâu", "hazu-expected":"lẽ ra / chắc hẳn", "tara-conditional":"nếu / khi", "ba-conditional":"nếu (điều kiện giả định)", "to-conditional":"hễ / cứ ... thì (kết quả tự nhiên)", "nara-conditional":"nếu là trường hợp đó; còn về", "volitional-form":"hãy cùng làm / tôi sẽ làm", "te-wa-ikenai-prohibition":"không được làm", "te-mo-ii-permission":"được phép làm", "nakereba-naranai":"phải / cần làm", "nakute-mo-ii":"không cần làm", "node-cause":"vì / do (cách nói mềm và khách quan)", "ga-kedo-although":"nhưng / mặc dù", "n-desu-explanation":"giải thích, nêu lý do hoặc nhấn nhẹ", "ni-naru-become":"trở thành", "ni-suru-decide":"chọn / quyết định là", "hajimeru-auxiliary":"bắt đầu làm", "owaru-finish":"làm xong", "sugiru-too-much":"quá / làm quá mức", "yasui-easy":"dễ làm", "nikui-hard":"khó làm", "noun-modifying-clause":"mệnh đề bổ nghĩa cho danh từ", "tari-tari-suru":"làm những việc như A, B", "jidoushi-tadoushi":"cặp nội động từ và ngoại động từ", "garu-third-person-emotion":"có vẻ muốn / có dấu hiệu cảm thấy (ngôi ba)", "kata-way-of-doing":"cách làm", "you-ni-suru":"cố gắng tạo thói quen / làm sao để", "te-kara-after-doing":"sau khi làm A thì làm B", "mae-ni-before-doing":"trước khi làm A", "ato-de-after-doing":"sau khi làm A", "koto-ga-dekiru":"có thể làm", "koto-ni-suru-decide":"tự quyết định làm / không làm", "koto-ni-naru-be-decided":"được quyết định là / trở thành quyết định", "nasai-command":"hãy làm (mệnh lệnh nhẹ)", "te-hoshii-want-someone":"muốn ai đó làm", "shi-reason-listing":"và; hơn nữa (liệt kê lý do/sự việc)", "you-to-omou-volitional-intent":"nghĩ là sẽ làm / dự định làm", "te-kureru-favor-received":"ai đó làm giúp tôi/nhóm của tôi", "te-morau-request-favor":"nhận sự giúp đỡ; nhờ ai làm", "te-ageru-favor-given":"làm giúp người ngoài nhóm của mình", "ageru-give-outward":"cho (từ phía mình ra bên ngoài)", "kureru-give-toward":"cho tôi / người thuộc nhóm của tôi", "morau-receive":"nhận", "o-v-kudasai-polite-honor":"xin vui lòng làm (lịch sự cao)", "sonkeigo-reru-rareru":"kính ngữ bằng thể bị động", "humble-o-suru":"khiêm nhường ngữ: tôi sẽ làm", "sou-iu-kou-iu":"loại như thế này / thế đó / thế kia", "tai-to-omou-want-to-think":"tôi nghĩ là muốn làm", "ba-ai-in-case":"trong trường hợp / nếu", "zutsu-each-per":"mỗi / theo từng", "tsumori-datta-had-intended":"đã định / vốn định", "hazu-datta-was-supposed":"lẽ ra đã / đáng lẽ", "demo-noun-even":"ngay cả; hay là ... gì đó", "te-itadaku-polite-favor-received":"khiêm nhường: được ai làm giúp", "ba-ii-should":"nên / chỉ cần làm", "yaru-casual-giving":"cho (thân mật, với người dưới/thú cưng/cây)", "v-temo-even-if":"dù cho / ngay cả khi", "irassharu-honorific":"kính ngữ của đi, đến, ở", "ossharu-honorific":"kính ngữ của nói", "goran-ni-naru-honorific":"kính ngữ của xem", "nasaru-honorific":"kính ngữ của làm", "mairu-humble":"khiêm nhường ngữ của đi, đến", "mousu-humble":"khiêm nhường ngữ của nói / tên là", "itadaku-humble-verb":"khiêm nhường ngữ của nhận, ăn, uống", "kudasaru-honorific-verb":"kính ngữ: người trên cho tôi/chúng tôi", "shika-nai":"chỉ có (đi với phủ định)", "ga-suki-kirai":"thích / ghét (dùng trợ từ が)", "ga-wakaru":"hiểu (dùng trợ từ が)", "ga-dekiru":"có thể / làm được (dùng trợ từ が)", "ga-kikoeru-mieru":"nghe thấy / nhìn thấy một cách tự nhiên", "dakara-so":"vì thế / do đó", "sorede-and-then":"vì vậy / rồi thì", "sorekara-after":"sau đó / hơn nữa", "shikashi-but":"nhưng / tuy nhiên (trang trọng)", "kedomo-formal-but":"nhưng / tuy nhiên", "toka-listing":"như là A, B (liệt kê không hết)", "tte-quotation":"rằng / người ta nói là (thân mật)", "soredemo-even-so":"dù vậy / tuy thế", "sou-da-appearance":"trông có vẻ / có vẻ như", "sou-da-hearsay":"nghe nói / có tin rằng", "you-ka-to-omou":"đang cân nhắc làm",
}

GROUPS = {
    1: {"n-desu-explanation", "te-itadaku-polite-favor-received", "o-v-kudasai-polite-honor"},
    2: {"potential-form", "koto-ga-dekiru", "ga-dekiru", "ga-kikoeru-mieru", "ga-suki-kirai", "ga-wakaru"},
    3: {"shi-reason-listing", "garu-third-person-emotion", "te-kara-after-doing"},
    4: {"jidoushi-tadoushi", "ni-naru-become", "owaru-finish"},
    5: {"darou-deshou-conjecture", "kamoshirenai-might", "hazu-expected"},
    6: {"tsumori-intention", "volitional-form", "you-to-omou-volitional-intent", "koto-ni-suru-decide", "koto-ni-naru-be-decided", "ni-suru-decide"},
    7: {"tara-conditional", "ba-ii-should", "te-mo-ii-permission", "nakute-mo-ii"},
    8: {"nasai-command", "te-wa-ikenai-prohibition", "te-hoshii-want-someone", "nakereba-naranai"},
    9: {"mae-ni-before-doing", "ato-de-after-doing", "tari-tari-suru"},
    10: {"ba-conditional", "nara-conditional", "v-temo-even-if", "ba-ai-in-case", "to-conditional"},
    11: {"you-ni-suru", "you-ka-to-omou"},
    12: {"passive-form"},
    13: {"noun-modifying-clause", "kata-way-of-doing", "sou-iu-kou-iu"},
    14: {"node-cause", "ga-kedo-although", "dakara-so", "sorede-and-then", "sorekara-after", "shikashi-but", "kedomo-formal-but"},
    15: {"tte-quotation", "toka-listing", "to-omou", "to-iu"},
    16: {"sonkeigo-reru-rareru", "irassharu-honorific", "ossharu-honorific", "goran-ni-naru-honorific", "nasaru-honorific", "kudasaru-honorific-verb"},
    17: {"tai-to-omou-want-to-think", "tsumori-datta-had-intended", "ta-koto-ga-aru", "te-morau-request-favor"},
    18: {"sou-da-appearance", "soredemo-even-so", "hazu-datta-was-supposed"},
    19: {"sugiru-too-much", "yasui-easy", "nikui-hard"},
    20: {"demo-noun-even", "shika-nai"},
    21: {"hajimeru-auxiliary", "te-kureru-favor-received", "zutsu-each-per"},
    22: {"sou-da-hearsay"},
    23: {"causative-form"},
    24: {"te-ageru-favor-given", "ageru-give-outward", "kureru-give-toward", "morau-receive", "yaru-casual-giving"},
    25: {"humble-o-suru", "mairu-humble", "mousu-humble", "itadaku-humble-verb"},
}
LESSON_FOR_ID = {pattern_id: order for order, pattern_ids in GROUPS.items() for pattern_id in pattern_ids}

def vietnamese_formula(formula: str) -> str:
    replacements = [("Plain form", "Thể thông thường"), ("dictionary form", "thể từ điển"), ("Verb stem", "gốc động từ"), ("Verb", "Động từ"), ("Noun", "Danh từ"), ("Quoted phrase", "Cụm được trích dẫn"), ("Clause", "Mệnh đề"), ("Number", "Số"), ("counter", "từ đếm"), ("form", "thể")]
    for source, target in replacements:
        formula = formula.replace(source, target)
    return formula

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    source_ids = {entry["id"] for entry in entries}
    if source_ids != set(VI) or source_ids != set(LESSON_FOR_ID):
        missing = source_ids - set(LESSON_FOR_ID)
        extra = set(LESSON_FOR_ID) - source_ids
        raise ValueError(f"Phân bài N4 chưa khớp nguồn. Thiếu: {sorted(missing)}. Thừa: {sorted(extra)}")
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM grammar_lessons WHERE level='N4'")
        for order, title in enumerate(LESSONS, start=1):
            db.execute("INSERT INTO grammar_lessons(level,title,description,order_index) VALUES ('N4',?,?,?)", (title, f"Bài {order + 25}: {title}." ,order))
        lessons = {order: ident for ident, order in db.execute("SELECT id,order_index FROM grammar_lessons WHERE level='N4'")}
        for entry in entries:
            meaning = VI[entry["id"]]
            note = f"Cách dùng: {meaning}. Hãy đối chiếu cấu trúc và các câu ví dụ bên dưới."
            cursor = db.execute("INSERT INTO grammar_patterns(lesson_id,formula,explanation_vi,note) VALUES (?,?,?,?)", (lessons[LESSON_FOR_ID[entry["id"]]], vietnamese_formula(entry["pattern"]), meaning, note))
            pattern_id = cursor.lastrowid
            for example in entry.get("examples", [])[:1]:
                db.execute("INSERT INTO grammar_examples(pattern_id,japanese,reading,meaning_vi) VALUES (?,?,?,?)", (pattern_id, example["japanese"], "", f"Ví dụ minh hoạ cho cách dùng: {meaning}."))
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n4_grammar_seed_version','n4-full-japanese-language-data-vi-v1')")
    print(f"Imported {len(entries)} N4 patterns into {len(LESSONS)} lessons.")

if __name__ == "__main__":
    main()
