"""Generate a reviewable Vietnamese draft for the N1 grammar importer."""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


def translate(text: str) -> str:
    query = urllib.parse.urlencode({
        "client": "gtx", "sl": "en", "tl": "vi", "dt": "t", "q": text,
    })
    request = urllib.request.Request(
        f"https://translate.googleapis.com/translate_a/single?{query}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return "".join(part[0] for part in payload[0] if part[0]).strip()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Không thể dịch nội dung.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("n1_vi.json"))
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    existing = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else {}
    for index, entry in enumerate(entries, 1):
        identifier = entry["id"]
        current = existing.setdefault(identifier, {})
        if not current.get("meaning"):
            current["meaning"] = translate(entry["meaning_en"])
        first_example = (entry.get("examples") or [{}])[0]
        if not current.get("example"):
            current["example"] = translate(first_example.get("english", ""))
        args.output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{index}/{len(entries)} {identifier}", flush=True)
        time.sleep(0.12)


if __name__ == "__main__":
    main()
