"""Apply KanjiAI-authored Vietnamese labels to the 77 imported N5 patterns."""
import argparse
import json
import re
import sqlite3
from pathlib import Path

from database import DB_PATH

MEANINGS = [
    "Là/ở (dạng lịch sự).", "Là/ở (dạng thông thường).", "Đã là/đã ở (dạng lịch sự).", "Không phải/không là (dạng lịch sự).",
    "Đuôi động từ lịch sự ở hiện tại hoặc tương lai.", "Đuôi động từ lịch sự ở quá khứ.", "Phủ định lịch sự ở hiện tại hoặc tương lai.", "Phủ định lịch sự ở quá khứ.",
    "Đánh dấu chủ đề của câu; đọc là wa.", "Đánh dấu chủ ngữ và thường đưa thông tin mới.", "Đánh dấu đối tượng trực tiếp của động từ.", "Chỉ đích đến, nơi tồn tại, thời điểm hoặc đối tượng nhận tác động.",
    "Chỉ phương tiện, công cụ hoặc nơi diễn ra hành động.", "Nối danh từ theo nghĩa và/cùng với.", "Chỉ sở hữu hoặc dùng danh từ này bổ nghĩa cho danh từ kia.", "Chỉ hướng di chuyển; đọc là e.",
    "Chỉ điểm bắt đầu: từ nơi chốn hoặc thời gian.", "Chỉ điểm kết thúc: đến, cho tới.", "Cũng, cũng là.", "Biến câu thành câu hỏi.",
    "Nhỉ/đúng không; tìm sự đồng tình hoặc xác nhận hiểu biết chung.", "Nhấn mạnh hoặc báo cho người nghe thông tin mới.", "Đây/đó/đằng kia/cái nào; đại từ chỉ đồ vật.", "Này/đó/kia/nào + danh từ; từ chỉ định đứng trước danh từ.",
    "Ở đây/ở đó/đằng kia/ở đâu; từ chỉ địa điểm.", "Có/tồn tại đối với vật vô tri.", "Có/tồn tại đối với người và động vật.", "Thể nối て, nền tảng của nhiều cấu trúc ghép.",
    "Hãy làm...; lời yêu cầu lịch sự.", "Đang làm... hoặc ở trạng thái đã làm xong.", "Thể phủ định thông thường của động từ.", "Thể quá khứ thông thường của động từ.",
    "Tính từ い ở hiện tại, dạng khẳng định.", "Phủ định tính từ い: không...", "Quá khứ tính từ い: đã...", "Tính từ な ở hiện tại.",
    "Tính từ な bổ nghĩa trực tiếp cho danh từ.", "Phủ định tính từ な.", "Quá khứ tính từ な.", "Chúng ta hãy...; thể ý chí lịch sự.",
    "Chúng ta cùng... nhé? / Tôi làm... nhé?", "Muốn làm...; mong muốn của người nói.", "Muốn có...; mong muốn của người nói.", "A ... hơn B; cấu trúc so sánh.",
    "Nhất; mức độ cao nhất trong một nhóm.", "Cách đếm chung cho đồ vật nhỏ: một, hai, ba...", "Cách đếm người.", "Từ để hỏi cơ bản: gì, ai, ở đâu, khi nào, thế nào, tại sao.",
    "Xin đừng làm...; lời yêu cầu phủ định lịch sự.", "X, Y, v.v.; liệt kê không đầy đủ.", "Bạn có muốn... không?; lời mời lịch sự.", "Đã làm rồi.",
    "Chưa / vẫn còn, tùy theo dạng động từ đi sau.", "Khi/vào thời điểm...", "Cùng với...", "Chỉ, chỉ có...",
    "Dạng trạng từ của tính từ い.", "Dạng trạng từ của tính từ な.", "Thể て của tính từ い; dùng để nối hoặc nêu nguyên nhân.", "Thể て của tính từ な và danh từ; dùng để nối hoặc nêu nguyên nhân.",
    "Cả X lẫn Y / không X cũng không Y.", "X và Y; liệt kê đầy đủ danh từ.", "Vị trí tương đối: trên, dưới, trong, trước, sau, cạnh, bên cạnh...",
    "Bao nhiêu / mấy tuổi.", "Bao nhiêu tiền / bao nhiêu.", "Mấy giờ.", "Thứ mấy / các ngày trong tuần.",
    "Cách đếm giờ.", "Cách đếm phút.", "Cách nói tuổi.", "Cách đếm tiền yên.",
    "Cách đếm vật dài, thon.", "Cách đếm vật mỏng, phẳng.", "Mỗi/từng, dùng với đơn vị thời gian.", "Đơn vị thời lượng: giờ.",
    "Đuôi lịch sự của tính từ い.", "Vì/do... nên...",
]

FORMULAS = {
    "desu-polite-copula": "N + です",
    "da-plain-copula": "N + だ",
    "deshita-past-polite-copula": "N + でした",
    "dewa-arimasen-negative-polite-copula": "N + ではありません",
    "masu-polite-verb": "Gốc Vます + ます",
    "mashita-polite-past-verb": "Gốc Vます + ました",
    "masen-polite-negative-verb": "Gốc Vます + ません",
    "masendeshita-polite-past-negative-verb": "Gốc Vます + ませんでした",
    "particle-wa-topic": "N + は",
    "particle-ga-subject": "N + が",
    "particle-o-object": "N + を",
    "particle-ni-target": "N / Địa điểm / Thời gian + に",
    "particle-de-means": "Địa điểm / N (phương tiện) + で",
    "particle-to-and-with": "N + と + V",
    "particle-no-possession": "N1 + の + N2",
    "particle-e-direction": "Địa điểm + へ",
    "particle-kara-from": "Địa điểm / Thời gian + から",
    "particle-made-until": "Địa điểm / Thời gian + まで",
    "particle-mo-also": "N + も",
    "particle-ka-question": "Câu + か",
    "particle-ne-seeking-agreement": "Câu + ね",
    "particle-yo-emphasis": "Câu + よ",
    "kore-sore-are-demonstratives": "これ / それ / あれ / どれ",
    "kono-sono-ano-dono-attributive": "この / その / あの / どの + N",
    "koko-soko-asoko-doko": "ここ / そこ / あそこ / どこ",
    "arimasu-existence-inanimate": "Địa điểm + に + N + が + あります",
    "imasu-existence-animate": "Địa điểm + に + N (người/động vật) + が + います",
    "te-form-basic": "Vて",
    "te-kudasai-request": "Vて + ください",
    "te-imasu-progressive": "Vて + います",
    "nai-form": "Vない",
    "ta-form": "Vた",
    "i-adjective-nonpast": "Aい + (です)",
    "i-adjective-negative": "Aい (bỏ い) + くない / くありません",
    "i-adjective-past": "Aい (bỏ い) + かった(です)",
    "na-adjective-nonpast": "Aな + です / だ",
    "na-adjective-attributive": "Aな + な + N",
    "na-adjective-negative": "Aな + ではありません / じゃない",
    "na-adjective-past": "Aな + でした / だった",
    "mashou-volitional": "Gốc Vます + ましょう",
    "mashou-ka-invitation": "Gốc Vます + ましょうか",
    "tai-desire": "Gốc Vます + たい",
    "ga-hoshii-wanting-thing": "N + が + ほしい(です)",
    "hou-ga-comparative": "N1 + のほうが + N2 + より + Aい / Aな",
    "ichiban-superlative": "一番 + Aい / Aな",
    "counter-tsu": "Số + つ",
    "counter-people-nin": "Số + 人（にん）",
    "question-words-basic": "何 / 誰 / どこ / いつ / どう / どうして",
    "nai-de-kudasai": "Vない + でください",
    "particle-ya-non-exhaustive": "N1 + や + N2 + (など)",
    "masenka-invitation": "Gốc Vます + ませんか",
    "mou-ta-already": "もう + Vた / ました",
    "mada-not-yet": "まだ + Vていない / まだ + Vている",
    "toki-ni-when-basic": "V (TTT) / Aい / Aな + な / N + の + とき(に)",
    "issho-ni-together": "N + と + 一緒に",
    "dake-only-basic": "N / Số + lượng từ + だけ",
    "i-adj-adverbial-ku": "Aい (bỏ い) + く (+ V)",
    "na-adj-adverbial-ni": "Aな + に (+ V)",
    "i-adj-te-joining-kute": "Aい (bỏ い) + くて",
    "na-adj-te-joining-de": "Aな / N + で",
    "mo-mo-both": "N1 + も + N2 + も",
    "to-exhaustive-listing": "N1 + と + N2",
    "location-nouns-ue-shita": "N + の + 上 / 下 / 中 / 前 / 後ろ / 横 / 隣 / 間 + (に / で / へ)",
    "ikutsu-how-many": "いくつ (+ lượng từ phù hợp nếu cần)",
    "ikura-how-much": "いくら",
    "nanji-what-time": "何時 (+ 〜分)",
    "nanyoubi-day-of-week": "何曜日 / 曜日",
    "counter-ji-oclock": "Số + 時",
    "counter-fun-minute": "Số + 分",
    "counter-sai-age": "Số + 歳 / 才",
    "counter-en-money": "Số + 円",
    "counter-hon-long": "Số + 本",
    "counter-mai-flat": "Số + 枚",
    "mai-every-prefix": "毎 + Thời gian",
    "jikan-time-duration": "Số + 時間",
    "i-adj-desu-politeness": "Aい + です",
    "kara-cause": "TTT / thể lịch sự + から",
}


def vietnamese_formula(formula: str) -> str:
    """Keep only grammar symbols and Vietnamese labels in learner-facing UI."""
    replacements = [
        ("Plain form", "TTT"), ("dictionary form", "thể từ điển"),
        ("Verb ます-stem", "Vます"), ("Verb stem", "Vます"),
        ("Verb-て form", "Vて"), ("Verb-た form", "Vた"),
        ("Verb-ない form", "Vない"), ("Verb", "V"), ("Noun", "N"),
        ("Sentence", "Câu"), ("Clause", "Mệnh đề"), ("Number", "Số"),
        ("counter", "trợ số"), ("form", "thể"),
    ]
    for source, target in replacements:
        formula = formula.replace(source, target)
    formula = formula.replace("Plain", "TTT").replace("plain", "TTT").replace("V plain", "V thể từ điển")
    formula = formula.replace("i-adjective", "Aい").replace("na-adjective", "Aな")
    formula = formula.replace("adjective", "tính từ").replace("root", "gốc").replace("stem", "gốc")
    for source, target in {"noun":"N", "verb":"V", "or":"hoặc", "and":"và", "of":"của", "basic":"cơ bản", "attributive":"bổ nghĩa", "exhaustive":"liệt kê đầy đủ", "non-exhaustive":"liệt kê không đầy đủ", "polite":"lịch sự"}.items():
        formula = re.sub(rf"\b{source}\b", target, formula, flags=re.I)
    return formula

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    if len(entries) != len(MEANINGS):
        raise ValueError("Source N5 count changed; review the Vietnamese mapping.")
    with sqlite3.connect(DB_PATH) as db:
        if set(FORMULAS) != {entry["id"] for entry in entries}:
            raise ValueError("Bảng công thức N5 không khớp inventory nguồn.")
        for entry, meaning in zip(entries, MEANINGS):
            db.execute("""UPDATE grammar_patterns SET formula=?, explanation_vi=?, note=?
                WHERE id IN (SELECT p.id FROM grammar_patterns p JOIN grammar_lessons l ON l.id=p.lesson_id
                WHERE l.level='N5' AND p.formula=?)""", (FORMULAS[entry["id"]], meaning, "Xem cấu trúc và ví dụ để nhận biết cách dùng trong câu.", entry["pattern"]))
        # Some older imported rows already had a partially localized formula
        # and therefore no longer match the source string above. Normalize
        # those rows too instead of leaving mixed English labels in the UI.
        # Patterns are inserted in source order; keeping that stable lets this
        # migration replace older partially localized formulas deterministically.
        current_rows = db.execute("""SELECT p.id,p.formula FROM grammar_patterns p
            JOIN grammar_lessons l ON l.id=p.lesson_id WHERE l.level='N5' ORDER BY p.id""").fetchall()
        if len(current_rows) != len(entries):
            raise ValueError("Số mẫu N5 trong cơ sở dữ liệu không khớp nguồn.")
        for (pattern_id, _), entry in zip(current_rows, entries):
            db.execute("UPDATE grammar_patterns SET formula=? WHERE id=?", (FORMULAS[entry["id"]], pattern_id))
    print(f"Localized {len(entries)} N5 pattern meanings and notes into Vietnamese.")

if __name__ == "__main__":
    main()
