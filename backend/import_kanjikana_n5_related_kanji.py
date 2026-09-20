"""Import the public “Kanji liên quan” lists for the 80 Kanjikana N5 kanji.

The resulting database is used locally; the app never requests Kanjikana at
runtime.  Re-run only to refresh this curated reference list.
"""
from __future__ import annotations

import re
import sqlite3
import time
import urllib.parse
import urllib.error
import urllib.request
from html import unescape

from database import DB_PATH, initialize_database
from import_kanjikana_n5 import KANJIKANA_N5

URL = "https://kanjikana.com/vi/kanji/{character}"
SECTION = re.compile(r'<div[^>]+class="[^"]*KanjiDetail_relatedKanji[^"]*"[^>]*>(.*?)</div>', re.S)
LINK = re.compile(r"<a\b(?P<attrs>[^>]*)>", re.S)
ATTRIBUTE = re.compile(r'''([\w:-]+)=(?:"([^"]*)"|'([^']*)')''')


def parse_related(html: str) -> list[tuple[str, str]]:
    match = SECTION.search(html)
    if not match:
        return []
    found: list[tuple[str, str]] = []
    for link in LINK.finditer(match.group(1)):
        attrs = {name: unescape(double or single or "") for name, double, single in ATTRIBUTE.findall(link.group("attrs"))}
        href = urllib.parse.unquote(attrs.get("href", ""))
        if not href.startswith("/vi/kanji/"):
            continue
        character = href.rsplit("/", 1)[-1]
        if len(character) == 1 and character not in {item[0] for item in found}:
            found.append((character, attrs.get("aria-label", "")))
    return found


def fetch(character: str) -> list[tuple[str, str]]:
    request = urllib.request.Request(URL.format(character=urllib.parse.quote(character)), headers={"User-Agent": "Mozilla/5.0 (KanjiAI educational data refresh)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return parse_related(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))
    return []


def main() -> None:
    initialize_database()
    rows: dict[str, list[tuple[str, str]]] = {}
    for character, _, _ in KANJIKANA_N5:
        related = fetch(character)
        if not related:
            raise RuntimeError(f"Không tìm được Kanji liên quan cho {character}")
        rows[character] = related
        print(f"{character}: {len(related)}")
        time.sleep(1.1)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("DELETE FROM kanji_related_characters WHERE kanji IN (SELECT char FROM kanji WHERE level='N5')")
        for character, related in rows.items():
            for order_index, (related_char, meaning) in enumerate(related, 1):
                db.execute("""INSERT INTO kanji_related_characters(kanji,related_char,meaning,order_index)
                    VALUES (?, ?, ?, ?)""", (character, related_char, meaning, order_index))
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n5_related_kanji_source','kanjikana-n5-v1')")
    print(f"Imported {sum(map(len, rows.values()))} related Kanji for {len(rows)} N5 kanji.")


if __name__ == "__main__":
    main()
