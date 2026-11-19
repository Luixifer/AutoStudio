"""No-network checks for the extra image model and independent QA."""
import base64
import unittest
from unittest.mock import patch
from scripts import flux2_klein_9b, vision_scout
from tests.test_vision_gemma import jpeg


class ScoutTests(unittest.TestCase):
    def test_scout_must_review_the_image_instead_of_prompt_only(self):
        answer = ("STAR: NO\nGAS_PLANET: YES\nDECISION: PASS\n"
                  "EVIDENCE: Two similarly shaded spherical planets are visible.")
        with patch.object(vision_scout, "_request", return_value={"response": answer}) as mock:
            verdict = vision_scout.evaluate_scout(
                jpeg(), "A hot gas world has a very short orbit.",
                "Huge star next to a gaseous planet.", "a" * 32, "secret")
        self.assertEqual(verdict["decision"], "FAIL")
        model, data, *_ = mock.call_args.args
        self.assertEqual(model, vision_scout.SCOUT_MODEL)
        parts = data["messages"][0]["content"]
        self.assertEqual(parts[1]["type"], "image_url")
        self.assertEqual(base64.b64decode(parts[1]["image_url"]["url"].split(",", 1)[1]), jpeg())

    def test_malformed_or_uncertain_never_passes(self):
        for s in ("", "PASS", "DECISION: PASS\nEVIDENCE: looks good",
                  "STAR: UNSURE\nGAS_PLANET: YES\nDECISION: PASS\nEVIDENCE: Star cannot be identified."):
            self.assertNotEqual(vision_scout.parse_scout(s)["decision"], "PASS")

    def test_two_passes_do_not_authorize_youtube(self):
        gate = vision_scout.independent_gate({"decision": "PASS"}, {"decision": "PASS"})
        self.assertEqual(gate["automated_result"], "AUTOMATED_PASS_ONLY")
        self.assertFalse(gate["ready_to_publish"])
        self.assertFalse(gate["human_visual_approved"])

    def test_hydrogen_scene_is_not_required_to_contain_a_star(self):
        good=("HYDROGEN: YES\nNO_TERRAIN: YES\nDECISION: PASS\n"
              "EVIDENCE: Two neutral spheres separate on a dark background.")
        bad=("HYDROGEN: NO\nNO_TERRAIN: NO\nDECISION: PASS\n"
             "EVIDENCE: Rocks and a glowing planet rather than hydrogen atoms.")
        self.assertEqual(vision_scout.parse_scout(good, scene_kind="hydrogen")["decision"], "PASS")
        self.assertEqual(vision_scout.parse_scout(bad, scene_kind="hydrogen")["decision"], "FAIL")
        with patch.object(vision_scout, "_request", return_value={"response": good}) as mocked:
            verdict=vision_scout.evaluate_scout(
                jpeg(), "Hydrogen molecules separate into neutral atoms.",
                "Two hydrogen atoms dissociate.", "a"*32, "token",
                scene_kind="hydrogen")
        self.assertEqual(verdict["decision"], "PASS")
        self.assertIn("HYDROGEN:", mocked.call_args.args[1]["messages"][0]["content"][0]["text"])

    def test_one_failure_vetoes(self):
        result = vision_scout.independent_gate({"decision": "PASS"}, {"decision": "FAIL"})
        self.assertEqual(result["automated_result"], "FAIL")


class FluxNineTests(unittest.TestCase):
    def test_9b_provider_uses_cloudflare_9b_endpoint_with_fixed_size(self):
        with self.assertRaises(ValueError):
            flux2_klein_9b.generate_klein9b("No credentials", "wrong", "bad")
        self.assertIn("flux-2-klein-9b", flux2_klein_9b.ENDPOINT_9B)
        self.assertEqual(flux2_klein_9b.WIDTH, 1536)
        self.assertEqual(flux2_klein_9b.HEIGHT, 864)


if __name__ == "__main__":
    unittest.main()
