#!/usr/bin/env python3
"""Download KanjiVG SVG files for the 380 Kanji in kanji_n2_full.json.

Files are written to public/kanjivg by default and named using a five-digit,
lowercase Unicode code point, e.g. 大 (U+5927) -> 05927.svg.
Existing non-empty SVGs are skipped.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji"
EXPECTED_COUNT = 380


def main() -> int:
    parser = argparse.ArgumentParser(description="Download KanjiVG SVGs for KanjiAI N2")
    parser.add_argument("--json", default=str(Path(__file__).with_name("kanji_n2_full.json")))
    parser.add_argument("--output", default="public/kanjivg")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--sleep", type=float, default=0.10)
    args = parser.parse_args()

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    entries = payload.get("kanji", [])
    chars = [x.get("kanji") for x in entries]
    if len(entries) != EXPECTED_COUNT or len(set(chars)) != EXPECTED_COUNT:
        raise SystemExit(f"JSON phải có đúng {EXPECTED_COUNT} Kanji duy nhất.")

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    skipped = 0
    failed = []

    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "KanjiAI-KanjiVG-Downloader/1.0")]

    for i, entry in enumerate(entries, start=1):
        ch = entry["kanji"]
        filename = f"{ord(ch):05x}.svg"
        dest = out_dir / filename

        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            print(f"[{i:03d}/{EXPECTED_COUNT}] SKIP {ch} -> {filename}")
            continue

        url = f"{args.base_url.rstrip('/')}/{filename}"
        last_error = None
        for attempt in range(1, args.retries + 1):
            try:
                with opener.open(url, timeout=args.timeout) as response:
                    body = response.read()
                if b"<svg" not in body[:4096] and b"<svg" not in body:
                    raise ValueError("response không phải SVG")
                dest.write_bytes(body)
                ok += 1
                print(f"[{i:03d}/{EXPECTED_COUNT}] OK   {ch} -> {filename}")
                last_error = None
                break
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as exc:
                last_error = exc
                if attempt < args.retries:
                    time.sleep(min(2 ** (attempt - 1), 4))

        if last_error is not None:
            failed.append((ch, filename, str(last_error)))
            print(f"[{i:03d}/{EXPECTED_COUNT}] FAIL {ch} -> {filename}: {last_error}")
        time.sleep(args.sleep)

    print("\n=== KanjiVG report ===")
    print(f"Tổng Kanji       : {EXPECTED_COUNT}")
    print(f"Tải thành công   : {ok}")
    print(f"Đã tồn tại/skip  : {skipped}")
    print(f"Thất bại         : {len(failed)}")
    if failed:
        print("\nCác file thất bại:")
        for ch, filename, err in failed:
            print(f"- {ch} {filename}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
