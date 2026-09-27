#!/usr/bin/env python3
"""Download KanjiVG SVG files for the 1,136 Kanji in kanji_n1_full.json.

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DEFAULT_BASE = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji"
EXPECTED_COUNT = 1136


def download_one(
    entry: dict,
    out_dir: Path,
    base_url: str,
    timeout: float,
    retries: int,
    sleep: float,
) -> tuple[str, str, str | None]:
    """Download one SVG using a private opener and an atomic local write."""
    ch = entry["kanji"]
    filename = f"{ord(ch):05x}.svg"
    dest = out_dir / filename
    url = f"{base_url.rstrip('/')}/{filename}"
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "KanjiAI-KanjiVG-Downloader/1.0")]
    last_error: Exception | None = None
    part = dest.with_name(f"{filename}.part")

    for attempt in range(1, retries + 1):
        try:
            with opener.open(url, timeout=timeout) as response:
                body = response.read()
            if b"<svg" not in body[:4096] and b"<svg" not in body:
                raise ValueError("response không phải SVG")
            part.write_bytes(body)
            part.replace(dest)
            if sleep:
                time.sleep(sleep)
            return ch, filename, None
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 4))

    if part.exists():
        part.unlink()
    return ch, filename, str(last_error)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download KanjiVG SVGs for KanjiAI N1")
    parser.add_argument("--json", default=str(Path(__file__).with_name("kanji_n1_full.json")))
    parser.add_argument("--output", default="public/kanjivg")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--sleep", type=float, default=0.10)
    parser.add_argument(
        "--workers", type=int, default=6,
        help="Số lượt tải đồng thời (1-12, mặc định 6).",
    )
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        parser.error("--workers phải trong khoảng 1 đến 12.")

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    entries = payload.get("kanji", [])
    chars = [x.get("kanji") for x in entries]
    if len(entries) != EXPECTED_COUNT or len(set(chars)) != EXPECTED_COUNT:
        raise SystemExit(f"JSON phải có đúng {EXPECTED_COUNT} Kanji duy nhất.")

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    pending = []
    skipped = 0
    for i, entry in enumerate(entries, start=1):
        filename = f"{ord(entry['kanji']):05x}.svg"
        if (out_dir / filename).exists() and (out_dir / filename).stat().st_size > 0:
            skipped += 1
        else:
            pending.append((i, entry))

    print(f"Tải {len(pending)} SVG còn thiếu (tối đa {args.workers} kết nối)...")
    ok = 0
    failed = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                download_one,
                entry,
                out_dir,
                args.base_url,
                args.timeout,
                args.retries,
                args.sleep,
            ): (i, entry["kanji"])
            for i, entry in pending
        }
        for completed, future in enumerate(as_completed(futures), 1):
            i, requested_ch = futures[future]
            ch, filename, error = future.result()
            if error:
                failed.append((ch, filename, error))
                print(f"[{i:04d}/{EXPECTED_COUNT}] FAIL {ch} -> {filename}: {error}")
            else:
                ok += 1
            if completed == len(pending) or completed % 50 == 0:
                print(f"Đã xử lý {completed}/{len(pending)} SVG còn thiếu.")

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
