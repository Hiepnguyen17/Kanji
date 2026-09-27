#!/usr/bin/env python3
"""
Scrape JLPT N3 Kanji data from Kanjikana and export a project-friendly JSON file.
Goals:
- keep fields useful for the project UI (stroke image, readings, radicals, vocab, related kanji)
- do NOT keep source URLs in final JSON output
- optionally download stroke-order SVG images into a local asset folder

Requirements:
    pip install requests beautifulsoup4 lxml

Usage:
    python scrape_kanjikana_n3_rich.py \
        --output kanji_n3_project_full.json \
        --assets-dir assets/kanji/strokes
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup, Tag

BASE = 'https://kanjikana.com'
LIST_PAGES = [
    'https://kanjikana.com/vi/kanji/jlpt/n3',
    *[f'https://kanjikana.com/vi/kanji/jlpt/n3/pages/{i}' for i in range(2, 9)]
]
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Codex scraper; +https://openai.com)',
    'Accept-Language': 'vi,en;q=0.8'
}


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text or '').strip()
    return text


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    resp = session.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'lxml')


def extract_detail_links(session: requests.Session) -> List[Dict]:
    results = []
    seen = set()
    order = 1
    for page_index, url in enumerate(LIST_PAGES, start=1):
        soup = get_soup(session, url)
        for a in soup.select('a[href]'):
            href = a.get('href', '').strip()
            text = clean_text(a.get_text(' ', strip=True))
            if not href.startswith('/vi/kanji/'):
                continue
            if '/jlpt/' in href or '/pages/' in href:
                continue
            # Usually list items look like: "部 phần"
            slug = href.rsplit('/', 1)[-1]
            if not slug:
                continue
            full_url = urljoin(BASE, href)
            # Deduplicate detail pages only
            if full_url in seen:
                continue
            # Only keep likely Kanji detail links
            if len(text) < 1:
                continue
            seen.add(full_url)
            kanji = text[0]
            meaning = clean_text(text[1:]) if len(text) > 1 else None
            results.append({
                'id': f'n3-{order:03d}',
                'kanji': kanji,
                'meaning': meaning,
                'jlpt': 'N3',
                'order': order,
                'sourcePage': page_index,
                'detailUrl': full_url,
            })
            order += 1
    # Keep only unique by kanji and stable order
    unique = []
    seen_kanji = set()
    for item in results:
        if item['kanji'] in seen_kanji:
            continue
        seen_kanji.add(item['kanji'])
        unique.append(item)
    return unique


def section_after_heading(soup: BeautifulSoup, heading_text: str) -> List[Tag]:
    heading = None
    for tag in soup.find_all(re.compile('^h[1-6]$')):
        if clean_text(tag.get_text()) == heading_text:
            heading = tag
            break
    if not heading:
        return []
    nodes = []
    for sib in heading.next_siblings:
        if isinstance(sib, Tag) and re.match(r'^h[1-6]$', sib.name or ''):
            break
        if isinstance(sib, Tag):
            nodes.append(sib)
    return nodes


def extract_first_int(text: str) -> Optional[int]:
    m = re.search(r'(\d+)\s*nét', text)
    return int(m.group(1)) if m else None


def split_readings(text: str) -> List[str]:
    text = clean_text(text)
    if not text:
        return []
    text = text.replace('、', ',')
    if text.startswith('Kun'):
        text = text[3:].strip()
    if text.startswith('On'):
        text = text[2:].strip()
    return [t.strip() for t in text.split(',') if t.strip()]


def extract_label_line(soup: BeautifulSoup, label: str) -> List[str]:
    for text in soup.stripped_strings:
        if text.startswith(label):
            return split_readings(text)
    return []


def extract_tags(soup: BeautifulSoup) -> Dict[str, object]:
    data = {'jlpt': None, 'themeTags': [], 'kanken': None}
    page_text = ' | '.join(soup.stripped_strings)
    m = re.search(r'JLPT\s*(N\d)', page_text)
    if m:
        data['jlpt'] = m.group(1)
    m = re.search(r'Kanken\s*(\d+)', page_text)
    if m:
        data['kanken'] = m.group(1)
    # Theme tags are typically links between JLPT and Kanken
    tags = []
    for a in soup.find_all('a'):
        t = clean_text(a.get_text())
        if not t:
            continue
        if t.startswith('JLPT ') or t.startswith('Kanken '):
            continue
        if t in {'Kanji', 'Kana', 'Công cụ', 'Từ thông dụng', 'Bộ thủ', 'Kanji liên quan', 'Tất cả ký tự', 'Theo cấp độ JLPT', 'Theo cấp độ Kanken', 'Theo bộ thủ', 'Theo chủ đề'}:
            continue
        # a conservative filter for page tags
        if len(t) <= 30 and ' ' in t and t not in tags:
            tags.append(t)
    data['themeTags'] = tags[:5]
    return data


def extract_radicals(soup: BeautifulSoup) -> List[str]:
    nodes = section_after_heading(soup, 'Bộ thủ')
    radicals = []
    for node in nodes:
        for a in node.find_all('a'):
            t = clean_text(a.get_text())
            if t and t not in radicals:
                radicals.append(t)
        if radicals:
            break
    return radicals


def extract_common_words(soup: BeautifulSoup) -> List[Dict[str, str]]:
    nodes = section_after_heading(soup, 'Từ thông dụng')
    lines = []
    for node in nodes:
        txt = clean_text(node.get_text('\n', strip=True))
        if txt:
            lines.extend([clean_text(x) for x in txt.split('\n') if clean_text(x)])
    # Parse pairs like:
    # 人間〖にんげん〗
    # con người...
    words = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '〖' in line and '〗' in line:
            meaning = lines[i+1] if i + 1 < len(lines) else ''
            m = re.match(r'^(.*?)〖(.*?)〗$', line)
            if m:
                words.append({
                    'word': clean_text(m.group(1)),
                    'reading': clean_text(m.group(2)),
                    'meaning': clean_text(meaning)
                })
            i += 2
        else:
            i += 1
    # dedupe
    out = []
    seen = set()
    for item in words:
        key = (item['word'], item['reading'])
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def extract_related_kanji(soup: BeautifulSoup) -> List[str]:
    nodes = section_after_heading(soup, 'Kanji liên quan')
    items = []
    for node in nodes:
        for a in node.find_all('a'):
            t = clean_text(a.get_text())
            if t and len(t) <= 3 and t not in items:
                items.append(t)
        txt = clean_text(node.get_text('\n', strip=True))
        if txt:
            for line in txt.split('\n'):
                line = clean_text(line)
                if line and len(line) <= 3 and line not in items:
                    items.append(line)
        if items:
            break
    return items[:10]


def guess_stroke_svg_url(kanji: str) -> str:
    hexcode = f'{ord(kanji):05x}'
    # Fallback source for downloading stroke SVG when the page HTML does not expose a direct asset URL.
    return f'https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{hexcode}.svg'


def download_file(session: requests.Session, url: str, dest: Path) -> bool:
    try:
        resp = session.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 200 and resp.content:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.content)
            return True
    except Exception:
        pass
    return False


def extract_page_title_parts(soup: BeautifulSoup) -> Dict[str, object]:
    text_blob = ' | '.join(soup.stripped_strings)
    return {
        'strokeCount': extract_first_int(text_blob),
        'onReadings': extract_label_line(soup, 'On'),
        'kunReadings': extract_label_line(soup, 'Kun')
    }


def scrape_detail(session: requests.Session, item: Dict, assets_dir: Path, download_images: bool = True) -> Dict:
    soup = get_soup(session, item['detailUrl'])
    title = clean_text(soup.title.get_text()) if soup.title else ''
    # title example: "人 - Ý nghĩa và chi tiết kanji"
    detail_kanji = title.split(' - ')[0].strip() if ' - ' in title else item['kanji']

    text_blob = ' | '.join(soup.stripped_strings)
    meaning = item.get('meaning') or None
    # Most pages have a single H1 line for main meaning
    for h1 in soup.find_all('h1'):
        t = clean_text(h1.get_text())
        if t and len(t) <= 80:
            meaning = t
            break

    meta = extract_page_title_parts(soup)
    tags = extract_tags(soup)
    radicals = extract_radicals(soup)
    vocab = extract_common_words(soup)
    related = extract_related_kanji(soup)

    hexcode = f'{ord(detail_kanji):05x}'
    local_rel = f'assets/kanji/strokes/{hexcode}.svg'
    local_path = assets_dir / f'{hexcode}.svg'

    # Try to find a direct SVG/GIF/PNG in the page first
    stroke_asset_url = None
    for tag in soup.find_all(['img', 'source']):
        candidate = tag.get('src') or tag.get('data-src') or tag.get('srcset')
        if not candidate:
            continue
        candidate = candidate.split()[0]
        if any(candidate.lower().endswith(ext) for ext in ('.svg', '.gif', '.png', '.webp')):
            stroke_asset_url = urljoin(BASE, candidate)
            break
    if not stroke_asset_url:
        stroke_asset_url = guess_stroke_svg_url(detail_kanji)

    downloaded = False
    if download_images:
        downloaded = download_file(session, stroke_asset_url, local_path)

    return {
        'id': item['id'],
        'kanji': detail_kanji,
        'meaning': meaning,
        'jlpt': tags['jlpt'] or item['jlpt'],
        'order': item['order'],
        'strokeCount': meta['strokeCount'],
        'onReadings': meta['onReadings'],
        'kunReadings': meta['kunReadings'],
        'radicals': radicals,
        'themeTags': tags['themeTags'],
        'kanken': tags['kanken'],
        'mnemonic': None,
        'strokeImage': {
            'fileName': f'{hexcode}.svg',
            'relativePath': local_rel,
            'downloaded': downloaded
        },
        'commonWords': vocab,
        'relatedKanji': related,
        '_debug': {
            'sourcePage': item.get('sourcePage'),
            'detailUrl': item.get('detailUrl'),
            'strokeAssetUrl': stroke_asset_url,
            'rawTextLength': len(text_blob)
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='kanji_n3_project_full.json')
    parser.add_argument('--assets-dir', default='assets/kanji/strokes')
    parser.add_argument('--sleep', type=float, default=0.4)
    parser.add_argument('--no-download-images', action='store_true')
    args = parser.parse_args()

    assets_dir = Path(args.assets_dir)
    session = requests.Session()

    seed = extract_detail_links(session)
    print(f'[INFO] Found {len(seed)} candidate kanji pages')

    data = []
    for idx, item in enumerate(seed, start=1):
        print(f'[INFO] ({idx}/{len(seed)}) {item["kanji"]}')
        try:
            enriched = scrape_detail(session, item, assets_dir, download_images=not args.no_download_images)
            data.append(enriched)
        except Exception as exc:
            print(f'[WARN] Failed {item["kanji"]}: {exc}')
        time.sleep(args.sleep)

    # Final pass: remove debug/source URLs from clean export if you do not want them in project data.
    clean_export = []
    for item in data:
        x = dict(item)
        x.pop('_debug', None)
        clean_export.append(x)

    out = {
        'meta': {
            'title': 'JLPT N3 Kanji - project data scraped from Kanjikana',
            'count': len(clean_export),
            'jlpt': 'N3',
            'language': 'vi'
        },
        'kanji': clean_export
    }
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[DONE] Wrote {args.output} with {len(clean_export)} entries')


if __name__ == '__main__':
    main()
