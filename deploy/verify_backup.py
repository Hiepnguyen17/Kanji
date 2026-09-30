"""Check a SQLite backup, optionally restore it to a separate new database."""
from __future__ import annotations

import argparse
from contextlib import closing
from pathlib import Path
import sqlite3


def verify(path: Path) -> dict[str, int]:
    with closing(sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit(f"Integrity check failed: {path}")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"kanji", "vocabulary", "grammar_patterns", "users", "user_progress"}
        if not required.issubset(tables):
            raise SystemExit(f"Missing tables in backup: {', '.join(sorted(required - tables))}")
        return {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in sorted(required)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument("--restore-to", type=Path, help="New separate destination; never overwrites")
    args = parser.parse_args()
    if not args.backup.is_file():
        raise SystemExit(f"Backup not found: {args.backup}")
    source_counts = verify(args.backup)
    print(f"Backup OK: {args.backup} | {source_counts}")
    if args.restore_to:
        destination = args.restore_to.resolve()
        if destination.exists():
            raise SystemExit(f"Refusing to overwrite: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(sqlite3.connect(f"{args.backup.resolve().as_uri()}?mode=ro", uri=True)) as source, closing(sqlite3.connect(destination)) as target:
                source.backup(target)
            restored_counts = verify(destination)
            if restored_counts != source_counts:
                raise SystemExit("Restored counts differ from backup")
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
        print(f"Restore OK: {destination} | {restored_counts}")
