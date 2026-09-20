"""Download the KanjiVG stroke-order SVGs used by the N5 lookup pages.

Run this only when refreshing local assets.  The application serves the
checked-in SVG files from ``public/kanjivg`` and never contacts KanjiVG at
runtime.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from import_kanjikana_n5 import KANJIKANA_N5


SOURCE = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{code}.svg"
OUTPUT = Path(__file__).parents[1] / "public" / "kanjivg"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []
    for character, _, _ in KANJIKANA_N5:
        code = f"{ord(character):05x}"
        target = OUTPUT / f"{code}.svg"
        request = urllib.request.Request(SOURCE.format(code=code), headers={"User-Agent": "KanjiAI asset refresh"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                target.write_bytes(response.read())
            print(f"OK {target.name}")
        except OSError as error:
            missing.append(character)
            print(f"ERROR {ord(character):05x}: {error}", file=sys.stderr)
    if missing:
        raise SystemExit("Không tải được: " + " ".join(missing))
    print(f"Đã lưu {len(KANJIKANA_N5)} SVG KanjiVG vào {OUTPUT}")


if __name__ == "__main__":
    main()
