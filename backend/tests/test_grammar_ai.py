"""No network or paid API call is made by these tests."""

import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import grammar_ai


class GrammarAITests(unittest.TestCase):
    def test_no_key_never_calls_network(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch("grammar_ai.requests.post") as post:
            with self.assertRaises(grammar_ai.GrammarAIError):
                grammar_ai.evaluate_grammar(123, formula="N + です", meaning="Tôi là học sinh.",
                                            reference="私は学生です。", answer="私は学生です。")
            post.assert_not_called()

    def test_server_only_request_and_structured_feedback(self):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"candidates": [{"content": {"parts": [{"text": json.dumps({
                    "verdict": "correct", "feedback": "Câu đúng.",
                })}]}}]}

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}), patch(
            "grammar_ai.requests.post", return_value=FakeResponse(),
        ) as post:
            result = grammar_ai.evaluate_grammar(456, formula="N + です", meaning="Tôi là học sinh.",
                                                 reference="私は学生です。", answer="私は学生です。")
        self.assertEqual(result, {"verdict": "correct", "feedback": "Câu đúng."})
        self.assertEqual(post.call_args.kwargs["headers"]["x-goog-api-key"], "test-key")
        self.assertIn("gemini-3.5-flash-lite:generateContent", post.call_args.args[0])
        self.assertEqual(post.call_args.kwargs["json"]["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(post.call_args.kwargs["json"]["generationConfig"]["responseSchema"]["required"], ["verdict", "feedback"])

    def test_rate_limit_is_explained_and_failed_call_does_not_use_daily_allowance(self):
        class RateLimitResponse:
            status_code = 429

            def raise_for_status(self):
                raise requests.HTTPError(response=self)

            def json(self):
                return {"error": {"code": 429, "message": "Resource exhausted"}}

        day = int(time.time() // 86400)
        before = grammar_ai._daily_usage[(day, 789)]
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}), patch(
            "grammar_ai.requests.post", return_value=RateLimitResponse(),
        ):
            with self.assertRaises(grammar_ai.GrammarAIError) as raised:
                grammar_ai.evaluate_grammar(789, formula="N + です", meaning="Tôi là học sinh.",
                                            reference="私は学生です。", answer="私は学生です。")
        self.assertEqual(raised.exception.status_code, 429)
        self.assertIn("giới hạn", str(raised.exception))
        self.assertEqual(grammar_ai._daily_usage[(day, 789)], before)

    def test_bad_key_is_explained_without_exposing_it(self):
        class ForbiddenResponse:
            status_code = 403

            def raise_for_status(self):
                raise requests.HTTPError(response=self)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-key"}), patch(
            "grammar_ai.requests.post", return_value=ForbiddenResponse(),
        ):
            with self.assertRaises(grammar_ai.GrammarAIError) as raised:
                grammar_ai.evaluate_grammar(790, formula="N + です", meaning="Tôi là học sinh.",
                                            reference="私は学生です。", answer="私は学生です。")
        self.assertIn("key không hợp lệ", str(raised.exception))
        self.assertNotIn("secret-key", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
