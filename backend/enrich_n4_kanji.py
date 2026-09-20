"""Apply locally curated display metadata to the imported N4 Kanji set.

This has no network dependency: readings and stroke counts already live in
the local database, while the Hán-Việt readings and radical glyphs come from
``n4_kanjikana.py``.
"""
from __future__ import annotations

from database import connect, initialize_database
from n4_kanjikana import KANJIKANA_N4, N4_HAN_VIET, N4_RADICALS


def main() -> None:
    initialize_database()
    with connect() as db:
        for character, _ in KANJIKANA_N4:
            db.execute(
                "UPDATE kanji SET han_viet=?, radical=? WHERE char=? AND level='N4'",
                (N4_HAN_VIET[character], N4_RADICALS[character], character),
            )
    print(f"Enriched {len(KANJIKANA_N4)} N4 Kanji metadata.")


if __name__ == "__main__":
    main()
