import unittest
from scripts.free_ai_audition import MODELS, audition, candidate_payload

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

if __name__ == "__main__":
    unittest.main()
