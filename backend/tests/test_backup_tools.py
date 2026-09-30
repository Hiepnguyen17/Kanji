"""Backup operation checks use disposable files only, never the production database."""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


DEPLOY_DIR = Path(__file__).resolve().parents[2] / "deploy"
sys.path.insert(0, str(DEPLOY_DIR))
from verify_backup import verify  # noqa: E402


class BackupToolsTests(unittest.TestCase):
    def test_pruning_only_removes_old_filename_matched_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = [f"kanjiai-2026090{day}T031500Z.db" for day in range(1, 5)]
            for name in names:
                (root / name).touch()
            (root / "other-data.db").touch()
            result = subprocess.run([sys.executable, str(DEPLOY_DIR / "prune_backups.py"),
                "--directory", str(root), "--keep", "2"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({path.name for path in root.iterdir()}, {names[2], names[3], "other-data.db"})

    def test_restored_database_is_separate_and_passes_integrity_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            backup, restored = root / "backup.db", root / "restored.db"
            with closing(sqlite3.connect(backup)) as db:
                for table in ("kanji", "vocabulary", "grammar_patterns", "users", "user_progress"):
                    db.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
                db.execute("INSERT INTO kanji(id) VALUES (1)")
                db.commit()
            result = subprocess.run([sys.executable, str(DEPLOY_DIR / "verify_backup.py"),
                "--backup", str(backup), "--restore-to", str(restored)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(verify(restored), verify(backup))
            self.assertEqual(verify(restored)["kanji"], 1)
