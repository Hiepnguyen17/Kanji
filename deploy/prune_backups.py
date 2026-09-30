"""Keep only the newest N filename-matched KanjiAI backup files."""
from __future__ import annotations

import argparse
from pathlib import Path
import re


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--keep", type=int, default=14)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.keep <= 365:
        raise SystemExit("--keep must be between 1 and 365")
    if args.directory.is_symlink():
        raise SystemExit("Backup directory must not be a symlink")
    directory = args.directory.resolve(strict=True)
    if not directory.is_dir():
        raise SystemExit("Backup directory must be a real directory")
    pattern = re.compile(r"kanjiai-\d{8}T\d{6}Z\.db\Z")
    backups = sorted((path for path in directory.iterdir()
        if pattern.fullmatch(path.name) and path.is_file() and not path.is_symlink()),
        key=lambda path: path.name, reverse=True)
    for path in backups[args.keep:]:
        if path.parent.resolve() != directory:
            raise SystemExit(f"Refusing path outside backup directory: {path}")
        print(f"{'Would remove' if args.dry_run else 'Removing'}: {path}")
        if not args.dry_run:
            path.unlink()
    print(f"Keeping {min(len(backups), args.keep)} backup file(s) in {directory}")
