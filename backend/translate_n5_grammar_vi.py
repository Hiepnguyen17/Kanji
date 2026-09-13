"""Create a clearly-labelled Vietnamese draft translation for imported N5 grammar.

This script is optional and contacts MyMemory's public translation endpoint.
Review the output before presenting it as teaching material.
"""
import argparse
import json
import sqlite3
import time
import urllib.parse
import urllib.request

from database import DB_PATH

API = "https://api.mymemory.translated.net/get"

def translate(text: str) -> str:
    query = urllib.parse.urlencode({"q": text, "langpair": "en|vi"})
    with urllib.request.urlopen(f"{API}?{query}", timeout=20) as response:
        payload = json.load(response)
    translated = payload.get("responseData", {}).get("translatedText", "")
    if not translated or translated == text:
        raise RuntimeError("translation service returned no usable text")
    return translated

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--field", choices=("meaning", "note", "examples"), required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        if args.field == "meaning":
            rows = db.execute("""SELECT p.id, p.explanation_vi AS text FROM grammar_patterns p
                JOIN grammar_lessons l ON l.id=p.lesson_id
                WHERE l.level='N5' AND p.explanation_vi GLOB '*[A-Za-z]*' ORDER BY p.id LIMIT ?""", (args.limit,)).fetchall()
            update = "UPDATE grammar_patterns SET explanation_vi=? WHERE id=?"
        elif args.field == "note":
            rows = db.execute("""SELECT p.id, p.note AS text FROM grammar_patterns p
                JOIN grammar_lessons l ON l.id=p.lesson_id
                WHERE l.level='N5' AND p.note GLOB '*[A-Za-z]*' ORDER BY p.id LIMIT ?""", (args.limit,)).fetchall()
            update = "UPDATE grammar_patterns SET note=? WHERE id=?"
        else:
            rows = db.execute("""SELECT e.id, e.meaning_vi AS text FROM grammar_examples e
                JOIN grammar_patterns p ON p.id=e.pattern_id JOIN grammar_lessons l ON l.id=p.lesson_id
                WHERE l.level='N5' AND e.meaning_vi GLOB '*[A-Za-z]*' ORDER BY e.id LIMIT ?""", (args.limit,)).fetchall()
            update = "UPDATE grammar_examples SET meaning_vi=? WHERE id=?"
        completed = 0
        for row in rows:
            try:
                result = translate(row["text"])
            except Exception as error:
                print(f"Skipped {row['id']}: {error}")
                continue
            db.execute(update, (result, row["id"]))
            completed += 1
            time.sleep(0.25)
    print(f"Translated {completed}/{len(rows)} {args.field} rows as machine-translation drafts.")

if __name__ == "__main__":
    main()
