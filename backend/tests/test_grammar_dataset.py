"""Content-level checks for the grammar dataset shipped with the application."""
from __future__ import annotations

from pathlib import Path
import sqlite3
import unittest


DATABASE_PATH = Path(__file__).resolve().parents[1] / "kanjiai.db"
EXPECTED_LEVELS = {"N1", "N2", "N3", "N4", "N5"}


class GrammarDatasetTests(unittest.TestCase):
    def test_every_jlpt_level_has_lessons_and_patterns(self):
        self.assertTrue(DATABASE_PATH.exists(), "Thiếu database nội dung sạch")
        uri = f"file:{DATABASE_PATH.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as db:
            lesson_counts = dict(db.execute("SELECT level, COUNT(*) FROM grammar_lessons GROUP BY level"))
            self.assertTrue(EXPECTED_LEVELS.issubset(lesson_counts))
            self.assertTrue(all(lesson_counts[level] > 0 for level in EXPECTED_LEVELS))

            empty_lessons = db.execute("""
                SELECT l.id FROM grammar_lessons l
                LEFT JOIN grammar_patterns p ON p.lesson_id = l.id
                GROUP BY l.id HAVING COUNT(p.id) = 0
            """).fetchall()
            self.assertEqual(empty_lessons, [])

            incomplete_patterns = db.execute("""
                SELECT id FROM grammar_patterns
                WHERE TRIM(formula) = '' OR TRIM(explanation_vi) = '' OR TRIM(note) = ''
            """).fetchall()
            self.assertEqual(incomplete_patterns, [])
