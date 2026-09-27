"""Create a consistent SQLite backup while the API is running."""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument("--source", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

source = Path(args.source)
output = Path(args.output)
if not source.is_file():
    raise SystemExit(f"Database not found: {source}")
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    raise SystemExit(f"Refusing to overwrite existing backup: {output}")

with sqlite3.connect(source) as source_db, sqlite3.connect(output) as backup_db:
    source_db.backup(backup_db)
    integrity = backup_db.execute("PRAGMA integrity_check").fetchone()[0]

if integrity != "ok":
    output.unlink(missing_ok=True)
    raise SystemExit(f"Backup failed integrity check: {integrity}")

print(output)