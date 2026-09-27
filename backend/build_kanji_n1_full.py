#!/usr/bin/env python3
"""
Build kanji_n1_full.json for KanjiAI from public sources.

Verified-source policy
----------------------
- Exact N1 character list/order + Vietnamese meaning/vocabulary:
  Kanjikana JLPT N1 pages / detail pages.
- Stroke count, On/Kun, Han-Viet, radical metadata:
  KANJIDIC-derived Vietnamese dataset:
  https://raw.githubusercontent.com/NVL4826/kanji-data-hanviet/master/kanji-jouyou.json
- SVG filename convention:
  KanjiVG (lowercase Unicode code point, padded to 5 hex digits).

The final JSON intentionally stores NO source URLs.

Quality behavior
----------------
This script FAILS instead of inventing data when:
- N1 list is not exactly 1,136 unique characters;
- a character has no trusted metadata;
- stroke count / radical / Han-Viet cannot be verified;
- vocabulary lacks reading or Vietnamese meaning.

Some rare characters and name kanji have fewer than four common words on the
Vietnamese source page. They are retained with the verified 0–8 entries that
exist rather than padded with unverified vocabulary. The build report records
that coverage so these entries can be enriched later.

Usage:
    pip install requests beautifulsoup4 lxml
    python build_kanji_n1_full.py --output kanji_n1_full.json

Optional cache:
    python build_kanji_n1_full.py --cache-dir .cache/kanjiai-n1
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, FeatureNotFound, Tag

EXPECTED_COUNT = 1136
BASE = "https://kanjikana.com"
LIST_BASE = f"{BASE}/vi/kanji/jlpt/n1"
HANVIET_URL = (
    "https://raw.githubusercontent.com/NVL4826/"
    "kanji-data-hanviet/master/kanji-jouyou.json"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (KanjiAI N1 dataset builder)",
    "Accept-Language": "vi,en;q=0.8",
}

# punctuation allowed in kana readings
KANA_RE = re.compile(r"^[\u3040-\u30ffー・〜～\-\s]+$")
TAG_RE = re.compile(r"<[^>]+>")

# `𠮟` is the sole Jōyō kanji in the N1 source list outside the BMP.  It was
# added to JIS X 0213 after many KANJIDIC-derived datasets were published, so
# the otherwise complete Hán-Việt source above has no record for it.  The
# values below are cross-checked against Kanjipedia's entry/word list and the
# Hán Nôm dictionary, which lists 𠮟 as a variant of 叱 (Hán-Việt: sất).
# Sources are deliberately kept out of the generated JSON.
SPECIAL_METADATA: Dict[str, Dict] = {
    "𠮟": {
        "meaning": "la mắng, khiển trách",
        "strokes": 5,
        "han_viet": ["sất"],
        "readings_on": ["シツ", "シチ"],
        "readings_kun": ["しか.る"],
        "bo": "khẩu 口 (+2 nét)",
        "commonWords": [
            {"word": "𠮟る", "reading": "しかる", "meaning": "la mắng"},
            {"word": "𠮟責", "reading": "しっせき", "meaning": "khiển trách"},
            {"word": "𠮟正", "reading": "しっせい", "meaning": "răn dạy, sửa lỗi"},
            {"word": "𠮟声", "reading": "しっせい", "meaning": "tiếng quở trách"},
            {"word": "𠮟咤", "reading": "しった", "meaning": "quát mắng lớn tiếng"},
            {"word": "𠮟咤激励", "reading": "しったげきれい", "meaning": "nghiêm khắc khích lệ"},
        ],
    },
    # Kanjikana lists the traditional form 剝.  The Hán-Việt dataset only
    # indexes its Japanese shinjitai counterpart 剥; the verified readings,
    # radical and 10-stroke count are shared by these listed variants.
    "剝": {
        "meaning": "ra khỏi, gọt, phai nhạt, đổi màu",
        "strokes": 10,
        "han_viet": ["bác"],
        "readings_on": ["ハク", "ホク"],
        "readings_kun": ["は.ぐ", "は.がす", "は.がれる", "へ.ぐ", "む.く", "む.ける"],
        "bo": "đao 刀 (+8 nét)",
        "commonWords": [],
    },
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def text_from_html(fragment: str) -> str:
    return clean(html.unescape(TAG_RE.sub("", fragment).replace("<!-- -->", "")))


def hiragana_to_katakana(value: str) -> str:
    out = []
    for c in value:
        o = ord(c)
        if 0x3041 <= o <= 0x3096:
            out.append(chr(o + 0x60))
        else:
            out.append(c)
    return "".join(out)


def normalize_reading(value: str, *, on: bool) -> str:
    value = clean(value)
    # KANJIDIC-style dot denotes okurigana boundary. Keep a learner-friendly
    # hyphen form but do not alter the underlying reading.
    value = value.replace(".", "-")
    return hiragana_to_katakana(value) if on else value


def get_text(session: requests.Session, url: str, cache: Optional[Path] = None) -> str:
    if cache and cache.exists() and cache.stat().st_size > 0:
        return cache.read_text(encoding="utf-8")
    r = session.get(url, headers=HEADERS, timeout=45)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    text = r.text
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text, encoding="utf-8")
    return text


def soup_for(session: requests.Session, url: str, cache: Optional[Path] = None) -> BeautifulSoup:
    html = get_text(session, url, cache)
    try:
        return BeautifulSoup(html, "lxml")
    except FeatureNotFound:
        # Keep the importer usable on a fresh Windows checkout where optional
        # lxml is not installed yet. The built-in parser is sufficient for the
        # selectors used by this controlled source.
        return BeautifulSoup(html, "html.parser")


def parse_expected_count(soup: BeautifulSoup) -> int:
    # Navigation contains labels such as "N1". Read the page description
    # instead, where Kanjikana publishes the total list size explicitly.
    description = soup.find("meta", attrs={"name": "description"})
    text = description.get("content", "") if description else ""
    m = re.search(r"(?:danh sách\s*)?(\d[\d,. ]*)\s*kanji", text, re.I)
    if not m:
        raise RuntimeError("Không đọc được số lượng Kanji từ mô tả trang N1.")
    return int(re.sub(r"[^\d]", "", m.group(1)))


def extract_list_page(soup: BeautifulSoup) -> List[Tuple[str, str, str]]:
    rows = []
    seen = set()
    for a in soup.select('a[href^="/vi/kanji/"]'):
        href = (a.get("href") or "").strip()
        if "/jlpt/" in href or "/pages/" in href:
            continue
        text = clean(a.get_text(" ", strip=True))
        if not text:
            continue
        ch = text[0]
        # only a single CJK character as item key
        if len(ch) != 1 or not (
            "\u3400" <= ch <= "\u4dbf" or
            "\u4e00" <= ch <= "\u9fff" or
            "\uf900" <= ch <= "\ufaff" or
            "\U00020000" <= ch <= "\U0002a6df"
        ):
            continue
        url = urljoin(BASE, href)
        if ch in seen:
            continue
        seen.add(ch)
        meaning = clean(text[1:]) or ""
        rows.append((ch, meaning, url))
    return rows


def fetch_n1_seed(session: requests.Session, cache_dir: Path) -> List[Dict]:
    first = soup_for(session, LIST_BASE, cache_dir / "list_01.html")
    expected = parse_expected_count(first)
    if expected != EXPECTED_COUNT:
        raise RuntimeError(
            f"Kanjikana hiện báo {expected} N1, script yêu cầu {EXPECTED_COUNT}. "
            "Không tiếp tục để tránh tạo sai dataset."
        )

    results = []
    seen = set()
    page = 1
    while len(results) < EXPECTED_COUNT and page <= 100:
        url = LIST_BASE if page == 1 else f"{LIST_BASE}/pages/{page}"
        soup = first if page == 1 else soup_for(
            session, url, cache_dir / f"list_{page:02d}.html"
        )
        rows = extract_list_page(soup)
        new_count = 0
        for ch, meaning, detail_url in rows:
            if ch in seen:
                continue
            seen.add(ch)
            results.append({
                "kanji": ch,
                "meaning_seed": meaning,
                "detail_url": detail_url,
            })
            new_count += 1
        if page > 1 and new_count == 0:
            break
        page += 1

    if len(results) != EXPECTED_COUNT:
        raise RuntimeError(
            f"Seed N1 phải đúng {EXPECTED_COUNT} ký tự, scrape được {len(results)}."
        )
    if len({x["kanji"] for x in results}) != EXPECTED_COUNT:
        raise RuntimeError("Seed N1 có ký tự trùng.")
    return results


def load_hanviet(session: requests.Session, cache_dir: Path) -> Dict:
    p = cache_dir / "kanji-jouyou.json"
    text = get_text(session, HANVIET_URL, p)
    data = json.loads(text)
    if not isinstance(data, dict) or len(data) < 1000:
        raise RuntimeError("Dataset metadata Hán-Việt không hợp lệ.")
    return data


def detail_cache_path(ch: str, cache_dir: Path) -> Path:
    return cache_dir / "details" / f"{ord(ch):05x}.html"


def prefetch_detail_pages(
    seed: List[Dict], cache_dir: Path, workers: int
) -> List[Dict[str, str]]:
    """Cache source pages with bounded concurrency before parsing them.

    Kanjikana detail pages are independent. Fetching them one at a time makes a
    full audit unnecessarily slow, while an unbounded request burst is impolite
    and fragile. Each worker uses its own Session because requests.Session is
    not thread-safe.
    """
    pending = [row for row in seed if not detail_cache_path(row["kanji"], cache_dir).exists()]
    if not pending:
        print("      Dùng lại cache chi tiết đã có.")
        return []

    print(f"      Tải {len(pending)} trang chưa có cache (tối đa {workers} kết nối)...")
    failures: List[Dict[str, str]] = []

    def fetch(row: Dict) -> str:
        with requests.Session() as worker_session:
            get_text(
                worker_session,
                row["detail_url"],
                detail_cache_path(row["kanji"], cache_dir),
            )
        return row["kanji"]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, row): row["kanji"] for row in pending}
        for completed, future in enumerate(as_completed(futures), 1):
            ch = futures[future]
            try:
                future.result()
            except Exception as exc:
                failures.append({"kanji": ch, "reason": f"tải trang chi tiết thất bại: {exc}"})
            if completed == len(pending) or completed % 50 == 0:
                print(f"      Đã tải {completed}/{len(pending)} trang chi tiết.")
    return failures


def extract_radical_symbol(meta: Dict) -> Optional[str]:
    # Example field: "ấp 邑 (+8 nét)" / "nhất 一 (+2 nét)"
    bo = clean(str(meta.get("bo") or ""))
    if not bo:
        return None
    before = bo.split("(+", 1)[0].strip()
    # Choose the final CJK character in the radical descriptor.
    candidates = re.findall(r"[\u2e80-\u2fdf\u3400-\u4dbf\u4e00-\u9fff]", before)
    return candidates[-1] if candidates else None


def section_nodes(soup: BeautifulSoup, title: str) -> List[Tag]:
    heading = None
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        if clean(h.get_text()) == title:
            heading = h
            break
    if not heading:
        return []
    out = []
    for node in heading.next_siblings:
        if isinstance(node, Tag) and re.match(r"^h[1-6]$", node.name or ""):
            break
        if isinstance(node, Tag):
            out.append(node)
    return out


def parse_vocab(soup: BeautifulSoup) -> List[Dict[str, str]]:
    # Kanjikana renders each common word as a list item.  The former sibling
    # parser missed this list because it sits next to the section heading,
    # rather than beneath it.
    word_list = soup.select_one('ul[class*="KanjiDetail_words"]')
    if word_list:
        vocab: List[Dict[str, str]] = []
        seen = set()
        for item in word_list.find_all("li", recursive=False):
            parts = item.find_all("div", recursive=False)
            if len(parts) < 2:
                continue
            heading = clean(parts[0].get_text(" ", strip=True))
            match = re.match(r"^(.*?)\s*【\s*(.*?)\s*】$", heading)
            if not match:
                continue
            word, reading = clean(match.group(1)), clean(match.group(2))
            meaning = clean(parts[1].get_text(" ", strip=True))
            if not word or not reading or not meaning or not KANA_RE.fullmatch(reading):
                continue
            key = (word, reading)
            if key not in seen:
                seen.add(key)
                vocab.append({"word": word, "reading": reading, "meaning": meaning})
        return vocab[:8]

    # Keep the fallback for an older version of the source page.
    nodes = section_nodes(soup, "Từ thông dụng")
    lines: List[str] = []
    for node in nodes:
        for s in node.stripped_strings:
            t = clean(s)
            if t:
                lines.append(t)

    vocab: List[Dict[str, str]] = []
    seen = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(.*?)〖(.*?)〗$", line)
        if not m:
            i += 1
            continue
        word = clean(m.group(1))
        reading = clean(m.group(2))
        meaning = clean(lines[i + 1]) if i + 1 < len(lines) else ""
        i += 2

        if not word or not reading or not meaning:
            continue
        if not KANA_RE.fullmatch(reading):
            continue
        key = (word, reading)
        if key in seen:
            continue
        seen.add(key)
        vocab.append({
            "word": word,
            "reading": reading,
            "meaning": meaning,
        })

    # Prefer concise common entries and preserve source order.
    return vocab[:8]


def parse_detail_fast(html_text: str, fallback_meaning: str) -> Tuple[str, List[Dict[str, str]]]:
    """Read Kanjikana's server-rendered word list without a full DOM parse.

    This fast path keeps a 1,136-page cached audit practical on a Windows
    checkout where optional lxml is not installed. Pages that do not match
    still fall through to the BeautifulSoup parser.
    """
    meaning = fallback_meaning
    heading = re.search(
        r'<h1[^>]*class="[^"]*KanjiDetail_meanings[^"]*"[^>]*>(.*?)</h1>',
        html_text,
        re.S,
    )
    if heading:
        candidate = text_from_html(heading.group(1))
        if candidate:
            meaning = candidate

    section = re.search(
        r'<ul[^>]*class="[^"]*KanjiDetail_words[^"]*"[^>]*>(.*?)</ul>',
        html_text,
        re.S,
    )
    if not section:
        return meaning, []

    vocab: List[Dict[str, str]] = []
    seen = set()
    for item in re.finditer(r"<li>(.*?)</li>", section.group(1), re.S):
        parts = re.findall(r"<div[^>]*>(.*?)</div>", item.group(1), re.S)
        if len(parts) < 2:
            continue
        heading_text = parts[0].replace("<!-- -->", "")
        match = re.search(r"<span[^>]*>(.*?)</span>\s*【\s*(.*?)\s*】", heading_text, re.S)
        if not match:
            continue
        word, reading = text_from_html(match.group(1)), text_from_html(match.group(2))
        word_meaning = text_from_html(parts[1])
        if not word or not reading or not word_meaning or not KANA_RE.fullmatch(reading):
            continue
        key = (word, reading)
        if key not in seen:
            seen.add(key)
            vocab.append({"word": word, "reading": reading, "meaning": word_meaning})
    return meaning, vocab[:8]


def parse_detail(
    session: requests.Session,
    ch: str,
    fallback_meaning: str,
    detail_url: str,
    cache_dir: Path,
) -> Tuple[str, List[Dict[str, str]]]:
    cache = detail_cache_path(ch, cache_dir)
    html_text = get_text(session, detail_url, cache)
    meaning, vocab = parse_detail_fast(html_text, fallback_meaning)
    if len(vocab) >= 4:
        return meaning, vocab

    soup = BeautifulSoup(html_text, "html.parser")

    meaning = fallback_meaning
    h1 = soup.find("h1")
    if h1:
        candidate = clean(h1.get_text())
        if candidate:
            meaning = candidate

    vocab = parse_vocab(soup)
    return meaning, vocab


def validate_entry(entry: Dict) -> List[str]:
    errors = []
    required = [
        "id", "kanji", "meaning", "hanViet", "jlpt", "order", "strokeCount",
        "onReadings", "kunReadings", "radicals", "strokeImage",
        "commonWords", "relatedKanji",
    ]
    for key in required:
        if key not in entry or entry[key] is None:
            errors.append(f"thiếu {key}")
    if entry.get("jlpt") != "N1":
        errors.append("jlpt != N1")
    if not isinstance(entry.get("strokeCount"), int) or entry["strokeCount"] <= 0:
        errors.append("strokeCount")
    if not entry.get("hanViet"):
        errors.append("hanViet")
    if not entry.get("radicals"):
        errors.append("radicals")
    if not isinstance(entry.get("commonWords"), list) or len(entry["commonWords"]) > 8:
        errors.append("commonWords")
    expected_svg = f"{ord(entry['kanji']):05x}.svg"
    if entry.get("strokeImage", {}).get("fileName") != expected_svg:
        errors.append("strokeImage")
    if entry.get("relatedKanji") != []:
        errors.append("relatedKanji phải []")
    return errors


def build_entry(
    idx: int, row: Dict, hv: Dict, cache_dir: Path
) -> Tuple[int, Optional[Dict], Optional[Dict[str, str]]]:
    """Build one validated entry from already cached source data."""
    ch = row["kanji"]
    special = SPECIAL_METADATA.get(ch)
    meta = hv.get(ch) or special
    if not meta:
        return idx, None, {"kanji": ch, "reason": "không có metadata trusted"}

    try:
        # A separate Session avoids sharing requests state between audit workers.
        with requests.Session() as detail_session:
            if special:
                meaning = special["meaning"]
                vocab = special["commonWords"]
            else:
                meaning, vocab = parse_detail(
                    detail_session, ch, row["meaning_seed"], row["detail_url"], cache_dir
                )
    except Exception as exc:
        return idx, None, {"kanji": ch, "reason": str(exc)}

    strokes = meta.get("strokes")
    han_viet = [clean(x) for x in (meta.get("han_viet") or []) if clean(x)]
    on = [
        normalize_reading(x, on=True)
        for x in (meta.get("readings_on") or [])
        if clean(x)
    ]
    kun = [
        normalize_reading(x, on=False)
        for x in (meta.get("readings_kun") or [])
        if clean(x)
    ]
    radical = extract_radical_symbol(meta)

    if not isinstance(strokes, int) or strokes <= 0:
        return idx, None, {"kanji": ch, "reason": "strokeCount chưa xác minh"}
    if not han_viet:
        return idx, None, {"kanji": ch, "reason": "Hán-Việt chưa xác minh"}
    if not radical:
        return idx, None, {"kanji": ch, "reason": "bộ thủ chưa xác minh"}

    filename = f"{ord(ch):05x}.svg"
    entry = {
        "id": f"n1-{idx:04d}",
        "kanji": ch,
        "meaning": meaning,
        "hanViet": ", ".join(x.upper() for x in han_viet),
        "jlpt": "N1",
        "order": idx,
        "strokeCount": strokes,
        "onReadings": on,
        "kunReadings": kun,
        "radicals": [radical],
        "strokeImage": {
            "fileName": filename,
            "relativePath": f"public/kanjivg/{filename}",
            "downloaded": False,
        },
        "commonWords": vocab,
        "relatedKanji": [],
    }
    errs = validate_entry(entry)
    if errs:
        return idx, None, {"kanji": ch, "reason": "; ".join(errs)}
    return idx, entry, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="kanji_n1_full.json")
    ap.add_argument("--cache-dir", default=".cache/kanjiai-n1")
    ap.add_argument("--sleep", type=float, default=0.15)
    ap.add_argument(
        "--workers",
        type=int,
        default=6,
        help="Số kết nối đồng thời khi cache trang nguồn (1-12, mặc định 6).",
    )
    ap.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Ghi JSON + unresolved report dù có mục không xác minh đủ. Mặc định fail.",
    )
    args = ap.parse_args()
    if not 1 <= args.workers <= 12:
        ap.error("--workers phải trong khoảng 1 đến 12.")

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    print("[1/4] Lấy danh sách N1...")
    seed = fetch_n1_seed(session, cache_dir)
    print(f"      {len(seed)} Kanji, unique={len({x['kanji'] for x in seed})}")

    print("[2/4] Lấy metadata KANJIDIC-derived/Hán-Việt...")
    hv = load_hanviet(session, cache_dir)

    print("[3/4] Cache trang nghĩa/từ vựng...")
    fetch_failures = prefetch_detail_pages(seed, cache_dir, args.workers)

    print("[4/4] Kiểm tra và dựng JSON...")
    unresolved = list(fetch_failures)
    completed: Dict[int, Tuple[Optional[Dict], Optional[Dict[str, str]]]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(build_entry, idx, row, hv, cache_dir): idx
            for idx, row in enumerate(seed, 1)
        }
        for count, future in enumerate(as_completed(futures), 1):
            idx, entry, error = future.result()
            completed[idx] = (entry, error)
            if count == len(futures) or count % 100 == 0:
                print(f"      Đã kiểm tra {count}/{len(futures)} Kanji.")

    entries = []
    for idx in range(1, len(seed) + 1):
        entry, error = completed[idx]
        if error:
            unresolved.append(error)
        elif entry:
            entries.append(entry)
        if args.sleep:
            time.sleep(args.sleep)

    unresolved_path = Path(args.output).with_name("n1_unresolved.json")
    unresolved_path.write_text(
        json.dumps(unresolved, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if unresolved and not args.allow_incomplete:
        raise SystemExit(
            f"FAIL: {len(unresolved)} Kanji chưa xác minh đủ. "
            f"Xem {unresolved_path}. Không tạo dataset giả."
        )

    chars = [x["kanji"] for x in entries]
    if not args.allow_incomplete:
        if len(entries) != EXPECTED_COUNT:
            raise SystemExit(
                f"FAIL: cần {EXPECTED_COUNT} entry hoàn chỉnh, hiện có {len(entries)}."
            )
        if len(set(chars)) != EXPECTED_COUNT:
            raise SystemExit("FAIL: có ký tự trùng.")

    vocabulary_coverage = {
        str(size): sum(1 for x in entries if len(x["commonWords"]) == size)
        for size in range(9)
    }
    payload = {
        "meta": {
            "title": "KanjiAI JLPT N1",
            "jlpt": "N1",
            "count": len(entries),
            "language": "vi",
            "expectedCount": EXPECTED_COUNT,
            "sourcesStoredInEntries": False,
            "commonWordCoverage": vocabulary_coverage,
        },
        "kanji": entries,
    }
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    vocab_total = sum(len(x["commonWords"]) for x in entries)
    print("\n=== Build report ===")
    print(f"Kanji hoàn chỉnh : {len(entries)}/{EXPECTED_COUNT}")
    print(f"Unique           : {len(set(chars))}")
    print(f"Từ vựng         : {vocab_total}")
    print(f"Phủ từ vựng     : {vocabulary_coverage}")
    print(f"Chưa xác minh    : {len(unresolved)}")
    print(f"Output           : {args.output}")
    return 0 if not unresolved else 2


if __name__ == "__main__":
    raise SystemExit(main())
