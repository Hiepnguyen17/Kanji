"""Complete the N5 vocabulary cards with short Japanese example sentences.

The vocabulary collection is imported from several N5 lesson sets.  Keeping the
completion rule here, rather than only editing ``kanjiai.db``, means a rebuilt
database receives the same examples.  Hand-curated examples already present in
the database are never replaced.
"""

from __future__ import annotations

import re
import sqlite3


N5_VOCABULARY_EXAMPLE_VERSION = "n5-context-examples-v1"


# These are intentionally conservative: a false positive produces a noticeably
# worse sentence than using the safe noun/phrase fallback below.
VERB_ENDINGS = ("する", "くる", "来る", "ある", "いる", "う", "く", "ぐ", "す", "つ", "ぬ", "ぶ", "む", "る")
I_ADJECTIVE_ENDINGS = ("い", "しい", "ない", "たい")
NA_ADJECTIVES = {
    "きれい", "静か", "しずか", "元気", "げんき", "有名", "ゆうめい", "便利", "べんり",
    "大丈夫", "だいじょうぶ", "簡単", "かんたん", "大切", "たいせつ", "必要", "ひつよう",
    "親切", "しんせつ", "暇", "ひま", "同じ", "おなじ", "上手", "じょうず", "下手", "へた",
}
PHRASE_WORDS = {
    "はい", "いいえ", "ありがとう", "すみません", "こんにちは", "こんばんは", "おはよう",
    "さようなら", "はじめまして", "お願いします", "ください", "もしもし", "ただいま",
    "いってきます", "いってらっしゃい", "いただきます", "ごちそうさまでした", "おやすみなさい",
    "失礼します", "おめでとうございます", "いらっしゃいませ",
}
FUNCTION_WORDS = {
    "です", "ます", "そうです", "そうですか", "これ", "それ", "あれ", "どれ", "ここ", "そこ",
    "あそこ", "どこ", "この", "その", "あの", "どの", "だれ", "何", "なに", "いつ", "どちら",
    "どなた", "いくら", "いくつ", "どんな", "どう", "そして", "でも", "から", "まで", "と",
    "も", "の", "は", "が", "を", "に", "で", "へ", "や", "ね", "よ", "か", "だけ", "しか",
    "まだ", "もう", "とても", "あまり", "たくさん", "少し", "ちょっと", "いつも", "時々",
    "あなた", "わたし", "私", "かれ", "彼", "かのじょ", "彼女", "さん", "ちゃん", "くん",
    "ええ", "ちがいます", "違います", "そう", "どうも", "どうぞ", "いちばん", "なぜ", "どうして",
}
LOCATION_HINTS = (
    "trường", "ga", "ngân hàng", "bưu điện", "bệnh viện", "thư viện", "công viên", "cửa hàng",
    "nhà hàng", "khách sạn", "sân bay", "nhà máy", "rạp", "hiệu sách", "nhà thuốc", "bãi đỗ",
)
PERSON_HINTS = (
    "giáo viên", "học sinh", "sinh viên", "bác sĩ", "nhân viên", "người", "đàn ông", "phụ nữ",
    "bạn bè", "khách", "bố", "mẹ", "anh trai", "chị gái", "em trai", "em gái", "ông", "bà",
)


def _meaning_head(meaning: str) -> str:
    """Return one clean Vietnamese gloss suitable for a short sentence."""
    head = re.split(r"[;,/]", meaning, maxsplit=1)[0]
    head = re.sub(r"\s*\([^)]*\)", "", head).strip()
    return (head or meaning.strip()).rstrip("。.！!")


def _sentence_gloss(meaning: str) -> str:
    """Lowercase a Vietnamese gloss when it appears in the middle of a sentence."""
    gloss = _meaning_head(meaning)
    return gloss[:1].lower() + gloss[1:] if gloss else gloss


def _is_verb(word: str) -> bool:
    if (
        word in PHRASE_WORDS
        or word in FUNCTION_WORDS
        or word in NA_ADJECTIVES
        or word.endswith(("です", "ます", "ました", "ません"))
        or any(mark in word for mark in "。！？!?「」『』")
    ):
        return False
    return word.endswith(VERB_ENDINGS)


def _is_i_adjective(word: str) -> bool:
    return (
        word.endswith(I_ADJECTIVE_ENDINGS)
        and word not in FUNCTION_WORDS | {"きらい", "嫌い"}
        and not any(mark in word for mark in "。！？!?「」『』")
    )


def _contains_hint(meaning: str, hints: tuple[str, ...]) -> bool:
    lower_meaning = meaning.lower()
    return any(hint in lower_meaning for hint in hints)


def build_example(word: str, reading: str, meaning: str) -> tuple[str, str, str]:
    """Build a simple, grammatical N5-level sentence around one vocabulary item."""
    gloss = _sentence_gloss(meaning)

    if (
        word in PHRASE_WORDS
        or word in FUNCTION_WORDS
        or word.endswith("です")
        or any(mark in word for mark in "。！？!?「」『』〜～")
    ):
        return (
            f"「{word}」は、よく 使う 言葉です。",
            f"「{reading}」は、よく つかう ことばです。",
            f"“{gloss}” là từ được dùng thường xuyên.",
        )
    if _is_verb(word):
        return (
            f"私は 毎日、{word}。",
            f"わたしは まいにち、{reading}。",
            f"Tôi thường {gloss} mỗi ngày.",
        )
    if _is_i_adjective(word):
        return (
            f"これは {word}です。",
            f"これは {reading}です。",
            f"Cái này {gloss}.",
        )
    if word in NA_ADJECTIVES:
        return (
            f"この 部屋は {word}です。",
            f"この へやは {reading}です。",
            f"Căn phòng này {gloss}.",
        )
    if _contains_hint(meaning, LOCATION_HINTS):
        return (
            f"私は {word}へ 行きます。",
            f"わたしは {reading}へ いきます。",
            f"Tôi đi đến {gloss}.",
        )
    if _contains_hint(meaning, PERSON_HINTS):
        return (
            f"あの 人は {word}です。",
            f"あの ひとは {reading}です。",
            f"Người kia là {gloss}.",
        )
    return (
        f"これは {word}です。",
        f"これは {reading}です。",
        f"Đây là {gloss}.",
    )


def _was_generated_by_previous_version(row: sqlite3.Row) -> bool:
    """Recognize rows created before provenance tracking was added."""
    word = row["word"]
    return row["example_japanese"] in {
        f"私は 毎日、{word}。",
        f"これは {word}です。",
        f"この 部屋は {word}です。",
        f"私は {word}へ 行きます。",
        f"あの 人は {word}です。",
        f"「{word}」と 言います。",
    }


def ensure_n5_vocabulary_examples(db: sqlite3.Connection) -> int:
    """Fill every incomplete N5 example without overwriting a curated card."""
    db.execute(
        """CREATE TABLE IF NOT EXISTS vocabulary_example_provenance (
            vocabulary_id INTEGER PRIMARY KEY REFERENCES vocabulary(id) ON DELETE CASCADE,
            generator_version TEXT NOT NULL
        )"""
    )
    rows = db.execute(
        """SELECT id, word, reading, meaning
           FROM vocabulary
           WHERE level = 'N5'
             AND (example_japanese = '' OR example_reading = '' OR example_meaning = '')"""
    ).fetchall()
    updates = [(*build_example(row["word"], row["reading"], row["meaning"]), row["id"]) for row in rows]
    db.executemany(
        """UPDATE vocabulary
           SET example_japanese = ?, example_reading = ?, example_meaning = ?
           WHERE id = ?""",
        updates,
    )
    db.executemany(
        "INSERT OR REPLACE INTO vocabulary_example_provenance(vocabulary_id, generator_version) VALUES (?, ?)",
        [(row["id"], N5_VOCABULARY_EXAMPLE_VERSION) for row in rows],
    )

    # The first run predated provenance tracking.  Rebuild only the recognisable
    # generated templates; hand-written entries have different sentences and
    # remain untouched.
    legacy_rows = db.execute(
        """SELECT id, word, reading, meaning, example_japanese
           FROM vocabulary
           WHERE level = 'N5'
             AND id NOT IN (SELECT vocabulary_id FROM vocabulary_example_provenance)"""
    ).fetchall()
    legacy_updates = [
        (*build_example(row["word"], row["reading"], row["meaning"]), row["id"])
        for row in legacy_rows if _was_generated_by_previous_version(row)
    ]
    db.executemany(
        """UPDATE vocabulary
           SET example_japanese = ?, example_reading = ?, example_meaning = ?
           WHERE id = ?""",
        legacy_updates,
    )
    db.executemany(
        "INSERT OR REPLACE INTO vocabulary_example_provenance(vocabulary_id, generator_version) VALUES (?, ?)",
        [(row[-1], N5_VOCABULARY_EXAMPLE_VERSION) for row in legacy_updates],
    )

    # Generated rows are owned by this helper, so improved rules can safely
    # refresh them.  Curated examples have no provenance row and are preserved.
    generated_rows = db.execute(
        """SELECT v.id, v.word, v.reading, v.meaning
           FROM vocabulary v
           JOIN vocabulary_example_provenance p ON p.vocabulary_id = v.id
           WHERE v.level = 'N5'"""
    ).fetchall()
    generated_updates = [
        (*build_example(row["word"], row["reading"], row["meaning"]), row["id"])
        for row in generated_rows
    ]
    db.executemany(
        """UPDATE vocabulary
           SET example_japanese = ?, example_reading = ?, example_meaning = ?
           WHERE id = ?""",
        generated_updates,
    )
    db.execute(
        "INSERT OR REPLACE INTO app_settings(key, value) VALUES (?, ?)",
        ("n5_vocabulary_examples_version", N5_VOCABULARY_EXAMPLE_VERSION),
    )
    return len(updates) + len(legacy_updates) + len(generated_updates)
