"""Small, repeatable quality repairs for grammar cards shown by the app."""

from __future__ import annotations

import sqlite3

from pykakasi import kakasi


GRAMMAR_QUALITY_VERSION = "grammar-reading-and-vi-audit-v1"

# These corrections address passive/word-for-word Vietnamese renderings found
# during the manual review.  Keys use the Japanese sentence so they remain
# stable even if lesson ordering changes.
MEANING_OVERRIDES = {
    "事故を契機に、安全対策を強化した。": "Sau vụ tai nạn, chúng tôi đã tăng cường các biện pháp an toàn.",
    "本日は定休日につき、閉店いたします。": "Vì hôm nay là ngày nghỉ định kỳ, cửa hàng chúng tôi xin đóng cửa.",
    "来月、東京に転勤することになりました。": "Từ tháng sau, tôi được điều chuyển công tác đến Tokyo.",
}


def _hiragana(text: str) -> str:
    return "".join(part["hira"] for part in kakasi().convert(text))


def ensure_grammar_quality(db: sqlite3.Connection) -> dict[str, int]:
    """Fill missing kana readings and apply reviewed Vietnamese corrections."""
    rows = db.execute(
        "SELECT id, japanese FROM grammar_examples WHERE COALESCE(reading, '') = ''"
    ).fetchall()
    db.executemany(
        "UPDATE grammar_examples SET reading = ? WHERE id = ?",
        [(_hiragana(row["japanese"]), row["id"]) for row in rows],
    )

    corrected = 0
    for japanese, meaning_vi in MEANING_OVERRIDES.items():
        result = db.execute(
            "UPDATE grammar_examples SET meaning_vi = ? WHERE japanese = ? AND meaning_vi <> ?",
            (meaning_vi, japanese, meaning_vi),
        )
        corrected += result.rowcount

    db.execute(
        "INSERT OR REPLACE INTO app_settings(key, value) VALUES (?, ?)",
        ("grammar_quality_version", GRAMMAR_QUALITY_VERSION),
    )
    return {"readings": len(rows), "translations": corrected}
