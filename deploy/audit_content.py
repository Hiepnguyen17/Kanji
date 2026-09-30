"""Read-only content audit. Never reads or prints learner/account tables."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET


def has_stroke_paths(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return False
    return any(element.tag.rsplit("}", 1)[-1] == "path" for element in root.iter())


def audit(db_path: Path, svg_root: Path) -> dict:
    if not db_path.is_file():
        raise SystemExit(f"Database does not exist: {db_path}")
    with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        def examples(sql: str) -> dict:
            rows = db.execute(sql).fetchall()
            return {"count": len(rows), "sample": [dict(row) for row in rows[:12]]}

        kanji = [dict(row) for row in db.execute("SELECT char,level FROM kanji")]
        missing_svg = [item for item in kanji if not has_stroke_paths(svg_root / f"{ord(item['char']):05x}.svg")]
        return {
            "database": str(db_path),
            "svg_root": str(svg_root),
            "counts": {
                "kanji": len(kanji),
                "vocabulary": db.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0],
                "grammar_patterns": db.execute("SELECT COUNT(*) FROM grammar_patterns").fetchone()[0],
            },
            "missing": {
                "kanji_fields": examples("""SELECT char,level FROM kanji WHERE TRIM(meaning)='' OR TRIM(han_viet)=''
                    OR TRIM(radical)='' OR strokes<1 OR (TRIM(on_reading)='' AND TRIM(kun_reading)='')"""),
                "kanji_svg": {"count": len(missing_svg), "sample": missing_svg[:12]},
                "vocabulary_fields": examples("""SELECT id,word,level FROM vocabulary
                    WHERE TRIM(word)='' OR TRIM(reading)='' OR TRIM(meaning)=''"""),
                "vocabulary_examples": examples("""SELECT id,word,level FROM vocabulary
                    WHERE TRIM(example_japanese)='' OR TRIM(example_meaning)=''"""),
                "grammar_fields": examples("""SELECT p.id,l.level FROM grammar_patterns p
                    JOIN grammar_lessons l ON l.id=p.lesson_id
                    WHERE TRIM(p.formula)='' OR TRIM(p.explanation_vi)=''"""),
                "grammar_examples": examples("""SELECT p.id,l.level FROM grammar_patterns p
                    JOIN grammar_lessons l ON l.id=p.lesson_id
                    WHERE NOT EXISTS (SELECT 1 FROM grammar_examples e WHERE e.pattern_id=p.id)"""),
            },
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("backend/kanjiai.db"))
    parser.add_argument("--svg-root", type=Path, default=Path("public/kanjivg"))
    args = parser.parse_args()
    print(json.dumps(audit(args.db, args.svg_root), ensure_ascii=False, indent=2))
