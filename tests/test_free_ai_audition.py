import unittest
import json
from unittest.mock import patch
from scripts.free_ai_audition import MODELS, audition, candidate_payload, run_candidate

PROMPT = "Review this documentary storyboard for scientific plausibility and shot diversity."

class FreeAIAuditionTests(unittest.TestCase):
    def test_dry_run_zero_cost(self):
        report = audition(PROMPT, ["gpt_oss_20b", "llama_4_scout"])
        self.assertEqual(report["calls_attempted"], 0)
        self.assertFalse(report["publish_allowed"])
        self.assertTrue(all(x["status"] == "planned" for x in report["candidates"]))

    def test_live_requires_explicit_budget(self):
        with self.assertRaises(ValueError):
            audition(PROMPT, ["gpt_oss_20b"], live=True, account="a"*32, token="secret")

    def test_budget_never_above_two(self):
        with self.assertRaises(ValueError):
            audition(PROMPT, ["gpt_oss_20b"], max_calls=3)

    def test_unknown_and_duplicate_models_rejected(self):
        for names in (["unknown"], ["gpt_oss_20b", "gpt_oss_20b"]):
            with self.assertRaises(ValueError):
                audition(PROMPT, names)

    def test_short_prompts_rejected(self):
        with self.assertRaises(ValueError):
            candidate_payload("gpt_oss_20b", "tiny")

    def test_live_fake_runner_does_not_approve(self):
        seen = []
        def fake(key, prompt, account, token):
            seen.append(key)
            return "Unverified observations only."
        report = audition(PROMPT, ["gpt_oss_20b"], live=True, max_calls=1,
                          account="a"*32, token="fake", runner=fake)
        self.assertEqual(seen, ["gpt_oss_20b"])
        self.assertFalse(report["editorial_approved"])
        self.assertFalse(report["publish_allowed"])

    def test_responses_api_extracts_only_final_output_text(self):
        payload = {"success": True, "result": {"output": [
            {"type": "reasoning", "summary": [{"type": "summary_text", "text": "private"}]},
            {"type": "message", "content": [{"type": "output_text", "text": "Check atmospheric claims."}]}
        ]}}
        class FakeResponse:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, limit):
                return json.dumps(payload).encode()
        result = run_candidate("gpt_oss_20b", PROMPT, "a"*32, "fake",
                               opener=lambda req, timeout: FakeResponse())
        self.assertEqual(result, "Check atmospheric claims.")

    def test_provider_reasoning_only_is_not_accepted(self):
        payload = {"success": True, "result": {"output": [
            {"type": "reasoning", "summary": [{"type": "summary_text", "text": "no final answer"}]}
        ]}}
        class FakeResponse:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, limit):
                return json.dumps(payload).encode()
        with self.assertRaises(ValueError):
            run_candidate("gpt_oss_20b", PROMPT, "a"*32, "fake",
                          opener=lambda req, timeout: FakeResponse())

if __name__ == "__main__":
    unittest.main()
