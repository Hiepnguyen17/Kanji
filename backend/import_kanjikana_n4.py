"""Import the Kanjikana N4 inventory with KANJIDIC2 readings and strokes."""
from __future__ import annotations

import sqlite3
from database import DB_PATH, initialize_database
from import_kanjikana_n5 import load_kanjidic2
from n4_kanjikana import KANJIKANA_N4, N4_HAN_VIET, N4_RADICALS

def main() -> None:
    initialize_database()
    wanted = {char for char, _ in KANJIKANA_N4}
    details = {}
    for entry in load_kanjidic2(None).findall("character"):
        char = entry.findtext("literal", "")
        if char not in wanted: continue
        readings = entry.findall("reading_meaning/rmgroup/reading")
        on = "・".join(item.text or "" for item in readings if item.get("r_type") == "ja_on")
        kun = "・".join(item.text or "" for item in readings if item.get("r_type") == "ja_kun")
        details[char] = (on, kun, int(entry.findtext("misc/stroke_count", "0")))
    missing = [char for char, _ in KANJIKANA_N4 if char not in details]
    if missing: raise ValueError("KANJIDIC2 thiếu: " + " ".join(missing))
    with sqlite3.connect(DB_PATH) as db:
        for index, (char, meaning) in enumerate(KANJIKANA_N4, 1):
            on, kun, strokes = details[char]
            radical = N4_RADICALS[char]
            db.execute("""INSERT INTO kanji(char,meaning,on_reading,kun_reading,strokes,level,radical,han_viet,order_index)
                VALUES (?, ?, ?, ?, ?, 'N4', ?, ?, ?)
                ON CONFLICT(char) DO UPDATE SET meaning=excluded.meaning,on_reading=excluded.on_reading,
                kun_reading=excluded.kun_reading,strokes=excluded.strokes,level='N4',radical=excluded.radical,
                han_viet=excluded.han_viet,order_index=excluded.order_index""", (char, meaning, on, kun, strokes, radical, N4_HAN_VIET[char], index))
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n4_kanji_source','kanjikana-order-kanjidic2-v1')")
    print(f"Imported {len(KANJIKANA_N4)} N4 kanji.")

if __name__ == '__main__': main()
