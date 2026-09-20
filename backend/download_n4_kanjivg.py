"""Download KanjiVG stroke-order SVGs for the Kanjikana JLPT N4 set.

Run only while refreshing checked-in assets.  The browser reads the local
``public/kanjivg`` files, so the learning pages do not depend on KanjiVG at
runtime.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from n4_kanjikana import KANJIKANA_N4


SOURCE = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{code}.svg"
OUTPUT = Path(__file__).parents[1] / "public" / "kanjivg"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []
    for character, _ in KANJIKANA_N4:
        code = f"{ord(character):05x}"
        target = OUTPUT / f"{code}.svg"
        if target.exists() and target.stat().st_size > 100:
            continue
        request = urllib.request.Request(
            SOURCE.format(code=code), headers={"User-Agent": "KanjiAI asset refresh"}
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                target.write_bytes(response.read())
            print(f"OK {target.name}")
        except OSError as error:
            missing.append(character)
            print(f"ERROR {code}: {error}", file=sys.stderr)
    if missing:
        raise SystemExit("Khong tai duoc: " + " ".join(missing))
    print(f"Da luu {len(KANJIKANA_N4)} SVG KanjiVG vao {OUTPUT}")


if __name__ == "__main__":
    main()
