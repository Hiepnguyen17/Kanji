"""Migration tests use a deliberately old SQLite schema in a temp directory."""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "legacy.db"
        self.previous_db_path = os.environ.get("KANJIAI_DB_PATH")
        os.environ["KANJIAI_DB_PATH"] = str(self.db_path)
        with sqlite3.connect(self.db_path) as db:
            db.executescript("""
                CREATE TABLE kanji (char TEXT PRIMARY KEY, meaning TEXT NOT NULL, on_reading TEXT NOT NULL, kun_reading TEXT NOT NULL, strokes INTEGER NOT NULL, level TEXT NOT NULL, radical TEXT NOT NULL);
                CREATE TABLE lessons (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', order_index INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE vocabulary (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_id INTEGER, word TEXT NOT NULL, reading TEXT NOT NULL, meaning TEXT NOT NULL, level TEXT NOT NULL);
                CREATE TABLE user_progress (user_id INTEGER NOT NULL, content_type TEXT NOT NULL, content_id TEXT NOT NULL, progress_state TEXT NOT NULL DEFAULT 'started', score REAL, updated_at INTEGER NOT NULL, PRIMARY KEY(user_id, content_type, content_id));
                CREATE TABLE user_review_items (user_id INTEGER NOT NULL, content_type TEXT NOT NULL, content_id TEXT NOT NULL, created_at INTEGER NOT NULL, PRIMARY KEY(user_id, content_type, content_id));
                INSERT INTO user_review_items(user_id,content_type,content_id,created_at) VALUES (7,'kanji','人',123);
            """)

    def tearDown(self):
        if self.previous_db_path is None:
            os.environ.pop("KANJIAI_DB_PATH", None)
        else:
            os.environ["KANJIAI_DB_PATH"] = self.previous_db_path
        self.temp_dir.cleanup()

    def test_legacy_schema_gains_required_columns_idempotently(self):
        import database
        database = importlib.reload(database)
        database.initialize_database()
        database.initialize_database()

        with sqlite3.connect(self.db_path) as db:
            columns = {
                table: {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
                for table in ("kanji", "lessons", "vocabulary", "user_progress", "user_review_items")
            }
            self.assertTrue({"han_viet", "order_index"}.issubset(columns["kanji"]))
            self.assertIn("group_id", columns["lessons"])
            self.assertTrue({"example_japanese", "example_reading", "example_meaning", "audio_url"}.issubset(columns["vocabulary"]))
            self.assertIn("resume_position", columns["user_progress"])
            self.assertTrue({"last_result", "reviewed_at", "review_count"}.issubset(columns["user_review_items"]))
            self.assertEqual(db.execute("SELECT content_id,last_result,review_count FROM user_review_items WHERE user_id=7").fetchone(), ("人", "new", 0))
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
