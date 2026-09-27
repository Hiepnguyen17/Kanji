#!/usr/bin/env python3
"""Import/upsert kanji_n1_full.json into a KanjiAI SQLite database.

Safety goals:
- never DELETE from kanji, users, user_sessions, or user_progress
- preserve an existing JLPT level (e.g. N5/N4/N3) when the same character already exists
- use SQLite UPSERT: ON CONFLICT(char) DO UPDATE
- upsert related vocabulary without deleting existing learner/project data
- validate the 1,136-entry N1 JSON before writing

Examples:
    python import_kanjikana_n1.py --db backend/kanjiai.db --json kanji_n1_full.json
    python import_kanjikana_n1.py --db app.db --dry-run
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

EXPECTED_COUNT = 1136

# Logical JSON field -> likely SQLite column names in KanjiAI-style schemas.
KANJI_COLUMN_CANDIDATES = {
    "meaning": ["meaning_vi", "meaning", "meanings"],
    "hanViet": ["han_viet", "hanViet", "hanviet", "sino_vietnamese"],
    "jlpt": ["jlpt", "jlpt_level", "level"],
    "order": ["display_order", "sort_order", "order_index", "n1_order", "order"],
    "strokeCount": ["stroke_count", "strokes", "strokeCount"],
    "onReadings": ["on_reading", "on_readings", "onyomi", "on_yomi", "onReadings"],
    "kunReadings": ["kun_reading", "kun_readings", "kunyomi", "kun_yomi", "kunReadings"],
    "radicals": ["radical", "radicals"],
    "strokeImage": ["stroke_image", "stroke_image_path", "svg_path", "image_path"],
}

WORD_COLUMN_CANDIDATES = {
    "word": ["word", "related_word", "vocabulary"],
    "reading": ["reading", "kana", "yomi"],
    "meaning": ["meaning", "meaning_vi", "translation"],
}


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def table_columns(conn: sqlite3.Connection, table: str) -> Dict[str, sqlite3.Row]:
    return {row["name"]: row for row in conn.execute(f"PRAGMA table_info({qident(table)})")}


def choose_column(columns: Dict[str, sqlite3.Row], candidates: Sequence[str]) -> Optional[str]:
    for c in candidates:
        if c in columns:
            return c
    return None


def encode_value(logical_field: str, entry: Dict[str, Any], column_name: str) -> Any:
    value = entry[logical_field]
    if logical_field in {"onReadings", "kunReadings", "radicals"}:
        # KanjiAI displays these TEXT fields with Japanese separators, rather
        # than rendering a JSON array in the lookup panel.
        return "・".join(value)
    if logical_field == "strokeImage":
        # DB normally needs the local path, not the whole JSON object.
        return value["relativePath"]
    return value


def validate_dataset(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("kanji"), list):
        raise ValueError("JSON phải có object gốc và mảng 'kanji'.")

    entries = payload["kanji"]
    if len(entries) != EXPECTED_COUNT:
        raise ValueError(f"Cần đúng {EXPECTED_COUNT} Kanji, hiện có {len(entries)}.")

    chars = [x.get("kanji") for x in entries]
    if len(set(chars)) != EXPECTED_COUNT:
        duplicates = sorted({c for c in chars if chars.count(c) > 1})
        raise ValueError(f"Có Kanji trùng: {duplicates}")

    required = [
        "id", "kanji", "meaning", "hanViet", "jlpt", "order", "strokeCount",
        "onReadings", "kunReadings", "radicals", "strokeImage", "commonWords",
        "relatedKanji",
    ]

    problems: List[str] = []
    for i, item in enumerate(entries, start=1):
        missing = [k for k in required if k not in item or item[k] is None]
        if missing:
            problems.append(f"#{i} {item.get('kanji')}: thiếu {', '.join(missing)}")
            continue
        if item["jlpt"] != "N1":
            problems.append(f"#{i} {item['kanji']}: jlpt != N1")
        if item["order"] != i:
            problems.append(f"#{i} {item['kanji']}: order={item['order']} (mong đợi {i})")
        if not isinstance(item["strokeCount"], int) or item["strokeCount"] <= 0:
            problems.append(f"#{i} {item['kanji']}: strokeCount không hợp lệ")
        if not item["radicals"]:
            problems.append(f"#{i} {item['kanji']}: thiếu radical")
        if not isinstance(item["commonWords"], list) or len(item["commonWords"]) > 8:
            problems.append(f"#{i} {item['kanji']}: commonWords phải là mảng 0–8 từ")
        expected_svg = f"{ord(item['kanji']):05x}.svg"
        if item["strokeImage"].get("fileName") != expected_svg:
            problems.append(f"#{i} {item['kanji']}: sai tên SVG")
        for word in item["commonWords"]:
            if not all(word.get(k) for k in ("word", "reading", "meaning")):
                problems.append(f"#{i} {item['kanji']}: commonWords có mục thiếu trường")

    if problems:
        raise ValueError("Dữ liệu không hợp lệ:\n- " + "\n- ".join(problems[:50]))
    return entries


def build_kanji_upsert(conn: sqlite3.Connection) -> Tuple[str, List[Tuple[str, str]]]:
    if not table_exists(conn, "kanji"):
        raise RuntimeError("Không tìm thấy bảng 'kanji'. Script không tự tạo/xóa bảng để tránh phá schema dự án.")

    cols = table_columns(conn, "kanji")
    if "char" not in cols:
        raise RuntimeError("Bảng 'kanji' phải có cột UNIQUE/PRIMARY KEY tên 'char'.")

    mapped: List[Tuple[str, str]] = []  # (logical, actual)
    for logical, candidates in KANJI_COLUMN_CANDIDATES.items():
        actual = choose_column(cols, candidates)
        if actual:
            mapped.append((logical, actual))

    if not choose_column(cols, KANJI_COLUMN_CANDIDATES["meaning"]):
        raise RuntimeError("Không tìm thấy cột meaning trong bảng 'kanji'.")

    insert_cols = ["char"] + [actual for _, actual in mapped]
    placeholders = ", ".join("?" for _ in insert_cols)

    updates = []
    for logical, actual in mapped:
        q = qident(actual)
        if logical == "jlpt":
            # Do not turn an existing N5/N4 character into N1 merely because it is
            # also present in this N1 study list. Only fill a missing level.
            updates.append(
                f"{q} = CASE WHEN {qident('kanji')}.{q} IS NULL OR "
                f"TRIM(CAST({qident('kanji')}.{q} AS TEXT)) = '' "
                f"THEN excluded.{q} ELSE {qident('kanji')}.{q} END"
            )
        else:
            updates.append(f"{q} = excluded.{q}")

    sql = (
        f"INSERT INTO {qident('kanji')} ({', '.join(qident(c) for c in insert_cols)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT({qident('char')}) DO UPDATE SET {', '.join(updates)}"
    )
    return sql, mapped


def get_kanji_id(conn: sqlite3.Connection, char: str) -> Optional[int]:
    cols = table_columns(conn, "kanji")
    if "id" not in cols:
        return None
    row = conn.execute(
        f"SELECT {qident('id')} FROM {qident('kanji')} WHERE {qident('char')}=?", (char,)
    ).fetchone()
    return int(row[0]) if row else None


def unique_indexes(conn: sqlite3.Connection, table: str) -> List[List[str]]:
    result: List[List[str]] = []
    for row in conn.execute(f"PRAGMA index_list({qident(table)})"):
        # PRAGMA index_list: seq, name, unique, origin, partial
        if not row[2]:
            continue
        index_name = row[1]
        columns = [r[2] for r in conn.execute(f"PRAGMA index_info({qident(index_name)})")]
        result.append(columns)
    return result


def upsert_words(conn: sqlite3.Connection, entry: Dict[str, Any]) -> int:
    table = "kanji_related_words"
    if not table_exists(conn, table):
        raise RuntimeError(
            "Không tìm thấy bảng 'kanji_related_words'. Script không tự tạo bảng để tránh thay đổi schema."
        )

    cols = table_columns(conn, table)
    word_col = choose_column(cols, WORD_COLUMN_CANDIDATES["word"])
    reading_col = choose_column(cols, WORD_COLUMN_CANDIDATES["reading"])
    meaning_col = choose_column(cols, WORD_COLUMN_CANDIDATES["meaning"])
    order_col = choose_column(cols, ["order_index", "sort_order", "display_order"])
    if not all((word_col, reading_col, meaning_col)):
        raise RuntimeError("Bảng kanji_related_words thiếu cột word/reading/meaning tương thích.")

    # Support the common FK designs: kanji_id -> kanji.id OR char/kanji_char directly.
    fk_mode: str
    fk_col: str
    fk_value: Any
    if "kanji_id" in cols:
        kanji_id = get_kanji_id(conn, entry["kanji"])
        if kanji_id is None:
            raise RuntimeError("kanji_related_words dùng kanji_id nhưng bảng kanji không có id phù hợp.")
        fk_mode, fk_col, fk_value = "id", "kanji_id", kanji_id
    elif "kanji" in cols:
        # KanjiAI stores the character itself as the foreign key.
        fk_mode, fk_col, fk_value = "char", "kanji", entry["kanji"]
    elif "kanji_char" in cols:
        fk_mode, fk_col, fk_value = "char", "kanji_char", entry["kanji"]
    elif "char" in cols:
        fk_mode, fk_col, fk_value = "char", "char", entry["kanji"]
    else:
        raise RuntimeError("Không tìm thấy kanji_id/kanji_char/char trong kanji_related_words.")

    target = [fk_col, word_col, reading_col]
    indexes = unique_indexes(conn, table)
    has_unique_target = any(set(idx) == set(target) and len(idx) == 3 for idx in indexes)

    affected = 0
    for order, word in enumerate(entry["commonWords"], start=1):
        values = [fk_value, word["word"], word["reading"], word["meaning"]]
        insert_cols = [fk_col, word_col, reading_col, meaning_col]
        if order_col:
            insert_cols.append(order_col)
            values.append(order)
        if has_unique_target:
            updates = [f"{qident(meaning_col)}=excluded.{qident(meaning_col)}"]
            if order_col:
                updates.append(f"{qident(order_col)}=excluded.{qident(order_col)}")
            sql = (
                f"INSERT INTO {qident(table)} ({', '.join(qident(c) for c in insert_cols)}) "
                f"VALUES ({', '.join('?' for _ in insert_cols)}) "
                f"ON CONFLICT({', '.join(qident(c) for c in target)}) DO UPDATE SET "
                + ", ".join(updates)
            )
            conn.execute(sql, values)
        else:
            # Non-destructive idempotent fallback when the existing schema has no
            # matching UNIQUE constraint. Never deletes rows.
            updates = [f"{qident(meaning_col)}=?"]
            update_values: List[Any] = [word["meaning"]]
            if order_col:
                updates.append(f"{qident(order_col)}=?")
                update_values.append(order)
            update_sql = (
                f"UPDATE {qident(table)} SET {', '.join(updates)} "
                f"WHERE {qident(fk_col)}=? AND {qident(word_col)}=? AND {qident(reading_col)}=?"
            )
            cur = conn.execute(update_sql, update_values + [fk_value, word["word"], word["reading"]])
            if cur.rowcount == 0:
                conn.execute(
                    f"INSERT INTO {qident(table)} ({', '.join(qident(c) for c in insert_cols)}) "
                    f"VALUES ({', '.join('?' for _ in insert_cols)})",
                    values,
                )
        affected += 1
    return affected


def main() -> int:
    parser = argparse.ArgumentParser(description="Import KanjiAI JLPT N1 dataset safely into SQLite")
    parser.add_argument("--db", required=True, help="Đường dẫn file SQLite của KanjiAI")
    parser.add_argument("--json", default=str(Path(__file__).with_name("kanji_n1_full.json")))
    parser.add_argument("--dry-run", action="store_true", help="Validate + inspect schema rồi rollback")
    args = parser.parse_args()

    json_path = Path(args.json)
    db_path = Path(args.db)
    if not json_path.exists():
        print(f"[ERROR] Không thấy JSON: {json_path}", file=sys.stderr)
        return 2
    if not db_path.exists():
        print(f"[ERROR] Không thấy DB: {db_path}", file=sys.stderr)
        return 2

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    entries = validate_dataset(payload)
    print(f"[OK] JSON: {len(entries)} Kanji, {sum(len(x['commonWords']) for x in entries)} từ vựng")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        sql, mapped = build_kanji_upsert(conn)
        print("[INFO] Kanji columns:", ", ".join(f"{a}->{b}" for a, b in mapped))

        before_protected = {}
        for table in ("users", "user_sessions", "user_progress"):
            if table_exists(conn, table):
                before_protected[table] = conn.execute(f"SELECT COUNT(*) FROM {qident(table)}").fetchone()[0]

        existing_lower = 0
        jlpt_col = choose_column(table_columns(conn, "kanji"), KANJI_COLUMN_CANDIDATES["jlpt"])

        conn.execute("BEGIN")
        for entry in entries:
            if jlpt_col:
                row = conn.execute(
                    f"SELECT {qident(jlpt_col)} FROM {qident('kanji')} WHERE {qident('char')}=?",
                    (entry["kanji"],),
                ).fetchone()
                if row and row[0] and str(row[0]).upper() in {"N5", "N4", "N3", "5", "4", "3"}:
                    existing_lower += 1

            values = [entry["kanji"]] + [encode_value(logical, entry, actual) for logical, actual in mapped]
            conn.execute(sql, values)

        word_count = 0
        for entry in entries:
            word_count += upsert_words(conn, entry)

        # Final DB check: every seed character must now exist exactly once by char.
        placeholders = ",".join("?" for _ in entries)
        db_count = conn.execute(
            f"SELECT COUNT(DISTINCT {qident('char')}) FROM {qident('kanji')} "
            f"WHERE {qident('char')} IN ({placeholders})",
            [x["kanji"] for x in entries],
        ).fetchone()[0]
        if db_count != EXPECTED_COUNT:
            raise RuntimeError(f"Kiểm tra DB thất bại: chỉ tìm thấy {db_count}/{EXPECTED_COUNT} ký tự.")

        # Prove protected tables were untouched by this transaction.
        for table, before in before_protected.items():
            after = conn.execute(f"SELECT COUNT(*) FROM {qident(table)}").fetchone()[0]
            if after != before:
                raise RuntimeError(f"Bảng bảo vệ {table} thay đổi số bản ghi: {before} -> {after}")

        if args.dry_run:
            conn.rollback()
            print("[DRY RUN] Validation thành công; đã rollback, DB không thay đổi.")
        else:
            conn.commit()
            print("[DONE] Import thành công.")

        print(f"  - Kanji trong file: {EXPECTED_COUNT}")
        print(f"  - Kanji seed có mặt trong DB: {db_count}")
        print(f"  - Related words xử lý: {word_count}")
        print(f"  - Ký tự đã có level N5/N4/N3 và được giữ nguyên level: {existing_lower}")
        return 0

    except Exception as exc:
        conn.rollback()
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
