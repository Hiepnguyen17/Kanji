"""Small HTTP-level regression tests for the public learner API."""
from __future__ import annotations

import importlib
import gc
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.previous_env = {name: os.environ.get(name) for name in (
            "KANJIAI_DB_PATH", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "KANJIAI_ADMIN_API_KEY",
        )}
        os.environ["KANJIAI_DB_PATH"] = str(Path(cls.temp_dir.name) / "api-test.db")
        os.environ["GOOGLE_CLIENT_ID"] = ""
        os.environ["GOOGLE_CLIENT_SECRET"] = ""
        os.environ["KANJIAI_ADMIN_API_KEY"] = ""

        import database
        import main
        importlib.reload(database)
        cls.main = importlib.reload(main)
        cls.client = TestClient(cls.main.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls.client.close()
        del cls.main
        gc.collect()
        # SQLite handles can be released one scheduler tick after FastAPI's
        # lifespan closes on Windows.
        for _ in range(5):
            try:
                cls.temp_dir.cleanup()
                break
            except PermissionError:
                time.sleep(0.1)
        for name, value in cls.previous_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_health_and_kanji_list_are_available(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

        response = self.client.get("/api/kanji?level=N5")
        self.assertEqual(response.status_code, 200)
        items = response.json()
        self.assertGreaterEqual(len(items), 9)
        self.assertTrue({"char", "meaning", "on_reading", "kun_reading", "level"}.issubset(items[0]))

    def test_unknown_kanji_returns_not_found_and_admin_stays_closed(self):
        self.assertEqual(self.client.get("/api/kanji/龘").status_code, 404)
        self.assertEqual(self.client.get("/admin/content-audit").status_code, 503)
        self.assertEqual(self.client.post("/api/handwriting/samples", json={"image": "x", "expected_text": "日"}).status_code, 503)

    def test_grammar_ai_requires_login_and_server_key(self):
        with self.main.connect() as db:
            pattern_id = db.execute("SELECT id FROM grammar_patterns LIMIT 1").fetchone()[0]
        url = f"/grammar/patterns/{pattern_id}/evaluate"
        body = {"meaning": "Tôi là học sinh.", "reference": "私は学生です。", "answer": "私は学生です。"}
        self.assertEqual(self.client.post(url, json=body).status_code, 401)
        now = int(time.time())
        token = "grammar-ai-test-user"
        with self.main.connect() as db:
            user_id = db.execute("INSERT INTO users(google_sub,email,display_name,created_at,last_login_at) VALUES (?,?,?,?,?)",
                                 ("grammar-ai-test", "grammar-ai@example.test", "Test", now, now)).lastrowid
            db.execute("INSERT INTO user_sessions(token_hash,user_id,expires_at,created_at) VALUES (?,?,?,?)",
                       (self.main.session_digest(token), user_id, now + 3600, now))
        self.client.cookies.set("kanjiai_session", token)
        try:
            with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
                self.assertEqual(self.client.post(url, json=body).status_code, 503)
            with patch("main.evaluate_grammar", return_value={"verdict": "correct", "feedback": "Câu đúng."}) as grader:
                self.assertEqual(self.client.post(url, json=body).json(), {"verdict": "correct", "feedback": "Câu đúng."})
                with self.main.connect() as db:
                    formula = db.execute("SELECT formula FROM grammar_patterns WHERE id=?", (pattern_id,)).fetchone()[0]
                self.assertEqual(grader.call_args.kwargs["formula"], formula)
            with patch("main.evaluate_grammar", side_effect=self.main.GrammarAIError("Gemini API đã đạt giới hạn sử dụng.", 429)):
                shortage = self.client.post(url, json=body)
                self.assertEqual(shortage.status_code, 429)
                self.assertIn("giới hạn", shortage.json()["detail"])
            self.assertEqual(self.client.post("/grammar/patterns/99999999/evaluate", json=body).status_code, 404)
        finally:
            self.client.cookies.clear()

    def test_review_results_are_persistent_prioritized_and_account_scoped(self):
        now = int(time.time())
        token_one, token_two = "review-test-user-one", "review-test-user-two"
        with self.main.connect() as db:
            first = db.execute("INSERT INTO users(google_sub,email,display_name,created_at,last_login_at) VALUES (?,?,?,?,?)",
                ("review-test-one", "review-one@example.test", "One", now, now)).lastrowid
            second = db.execute("INSERT INTO users(google_sub,email,display_name,created_at,last_login_at) VALUES (?,?,?,?,?)",
                ("review-test-two", "review-two@example.test", "Two", now, now)).lastrowid
            for user_id, token in ((first, token_one), (second, token_two)):
                db.execute("INSERT INTO user_sessions(token_hash,user_id,expires_at,created_at) VALUES (?,?,?,?)",
                    (self.main.session_digest(token), user_id, now + 3600, now))
            kanji = [row[0] for row in db.execute("SELECT char FROM kanji ORDER BY char LIMIT 2")]
            vocab_id = db.execute("SELECT id FROM vocabulary WHERE lesson_id IS NOT NULL LIMIT 1").fetchone()[0]
            grammar_id = db.execute("SELECT id FROM grammar_patterns LIMIT 1").fetchone()[0]
        try:
            self.client.cookies.set("kanjiai_session", token_one)
            for content_type, content_id in (("kanji", kanji[0]), ("kanji", kanji[1]),
                                             ("vocabulary", f"word-{vocab_id}"), ("grammar", f"pattern-{grammar_id}")):
                self.assertEqual(self.client.put(f"/review-items/{content_type}/{content_id}").status_code, 200)
            items = self.client.get("/review-items").json()
            self.assertEqual(len(items), 4)
            self.assertTrue(all(item["quiz_prompt"] and item["quiz_answer"] for item in items))
            self.assertTrue(all(item["last_result"] == "new" for item in items))

            remembered = self.client.put(f"/review-items/kanji/{kanji[0]}/result", json={"remembered": True})
            self.assertEqual(remembered.status_code, 200)
            self.assertEqual(remembered.json()["review_count"], 1)
            forgot = self.client.put(f"/review-items/kanji/{kanji[1]}/result", json={"remembered": False})
            self.assertEqual(forgot.status_code, 200)
            self.assertEqual(forgot.json()["last_result"], "forgot")
            ordered = self.client.get("/review-items").json()
            self.assertEqual(ordered[0]["content_id"], kanji[1])
            self.assertEqual(ordered[-1]["content_id"], kanji[0])

            self.client.cookies.set("kanjiai_session", token_two)
            self.assertEqual(self.client.get("/review-items").json(), [])
            self.assertEqual(self.client.put(f"/review-items/kanji/{kanji[1]}/result", json={"remembered": True}).status_code, 404)
            self.client.cookies.set("kanjiai_session", token_one)
            self.assertEqual(self.client.get("/review-items").json()[0]["last_result"], "forgot")
        finally:
            self.client.cookies.clear()

    def test_continue_learning_keeps_two_accounts_separate(self):
        now = int(time.time())
        tokens = ("progress-test-one", "progress-test-two")
        with self.main.connect() as db:
            lesson = db.execute("SELECT id,level FROM lessons WHERE level='N5' LIMIT 1").fetchone()
            grammar = db.execute("""SELECT l.id,l.level,p.id AS pattern_id FROM grammar_lessons l
                JOIN grammar_patterns p ON p.lesson_id=l.id LIMIT 1""").fetchone()
            for index, token in enumerate(tokens, 1):
                user_id = db.execute("INSERT INTO users(google_sub,email,display_name,created_at,last_login_at) VALUES (?,?,?,?,?)",
                    (f"progress-sub-{index}", f"progress-{index}@example.test", f"Learner {index}", now, now)).lastrowid
                db.execute("INSERT INTO user_sessions(token_hash,user_id,expires_at,created_at) VALUES (?,?,?,?)",
                    (self.main.session_digest(token), user_id, now + 3600, now))
        try:
            self.client.cookies.set("kanjiai_session", tokens[0])
            for kind, identifier, resume in (("kanji", "kanji-path:N5:day-002", 3),
                                              ("vocabulary", f"lesson-{lesson['id']}", 4),
                                              ("grammar", f"lesson-{grammar['id']}", grammar["pattern_id"])):
                response = self.client.put(f"/progress/{kind}/{identifier}", json={"progress_state": "started", "resume_position": resume})
                self.assertEqual(response.status_code, 200)
            own = self.client.get("/progress").json()
            self.assertEqual(len(own), 3)
            by_type = {item["content_type"]: item for item in own}
            self.assertEqual(by_type["kanji"]["href"], "/learn/kanji?level=N5&day=2")
            self.assertEqual(by_type["vocabulary"]["href"], f"/vocabulary/{lesson['level'].lower()}/lesson/{lesson['id']}/flashcard")
            self.assertEqual(by_type["vocabulary"]["resume_position"], 4)
            self.assertEqual(by_type["grammar"]["href"], f"/grammar/{grammar['level'].lower()}/lesson/{grammar['id']}/pattern/{grammar['pattern_id']}")

            self.client.cookies.set("kanjiai_session", tokens[1])
            self.assertEqual(self.client.get("/progress").json(), [])
            self.assertEqual(self.client.put("/progress/kanji/kanji-path:N5:day-002", json={"progress_state": "completed"}).status_code, 200)
            self.assertEqual(self.client.get("/progress").json()[0]["progress_state"], "completed")
            self.client.cookies.set("kanjiai_session", tokens[0])
            own_again = {item["content_type"]: item for item in self.client.get("/progress").json()}
            self.assertEqual(own_again["kanji"]["progress_state"], "started")
            self.assertEqual(own_again["kanji"]["resume_position"], 3)
        finally:
            self.client.cookies.clear()
