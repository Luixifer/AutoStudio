"""Offline safeguards for the image quality pilot."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import cinematic_pilot as cp
from scripts import shot_preflight as shots


def _story():
    return {"title": "KELT-9b", "scenes": [
        {"narration": f"Physical narrated event for scientific scene {i} is visible."}
        for i in range(1, 11)]}


def _plan():
    scales = shots.SCALES
    angles = shots.ANGLES
    roles = shots.ROLES
    return [
        {"scene": i, "scale": scales[i % len(scales)],
         "angle": angles[i % len(angles)],
         "role": roles[i % len(roles)],
         "subject": f"Unique celestial subject {i}",
         "visible_action": f"A separate celestial object number {i} moves past a distant illuminated star."}
        for i in range(1, 11)]


class CinematicPilotTests(unittest.TestCase):
    def test_bounded_prompts_exclude_unsupported_science(self):
        plan = _plan()
        for number in cp.PILOT_SCENES:
            prompt = cp.image_prompt(number, _story()["scenes"][number - 1]["narration"],
                                     plan[number - 1])
            self.assertLessEqual(len(prompt), 2000)
            self.assertIn("widescreen 16:9", prompt)
            self.assertIn("No humans", prompt)
        self.assertIn("NOT ionization", cp.image_prompt(6, "Hydrogen molecules separate in hot gas.", plan[5]))
        self.assertIn("no typography", cp.image_prompt(8, "An orbit takes only thirty-six hours.", plan[7]).lower())
        with self.assertRaises(ValueError):
            cp.image_prompt(2, "Narration for scene two long enough.", plan[1])

    def test_incomplete_or_invalid_signed_checkpoint_disallows_all_images(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "checkpoint.json"
            path.write_text("{}")
            calls = []
            def fake(*args):
                calls.append(1)
                return b""
            with self.assertRaises(ValueError):
                cp.pilot(_story(), path, Path(root) / "out",
                         "account", "token", live=True, generator=fake)
            self.assertEqual(calls, [])

    def test_live_uses_two_reviewers_with_hydrogen_specific_scope(self):
        from tests.test_vision_gemma import jpeg
        original=_story()
        planned=_plan()
        calls=[]
        def fake_scout(_img, _narration, _prompt, _account, _token, *, scene_kind):
            calls.append(scene_kind)
            return {"decision":"FAIL" if scene_kind=="hydrogen" else "PASS",
                    "evidence":"The claimed object cannot be established in the pixels."}
        with tempfile.TemporaryDirectory() as root:
            with patch.object(cp, "_read_checkpoint", return_value=(planned, 2)), \\
                 patch.object(cp, "validate_plan", return_value=planned), \\
                 patch.object(cp, "check_explicit_story_constraints", return_value=True):
                result=cp.pilot(
                    original,Path(root)/"checkpoint",Path(root)/"out",
                    "account","token",live=True,
                    generator=lambda *_args: jpeg(),
                    reviewer=lambda *_args: {"decision":"PASS",
                          "evidence":"Potentially acceptable image"},
                    scout_reviewer=fake_scout)
            self.assertEqual(calls,["orbit","hydrogen","orbit"])
            self.assertEqual(result["completed_image_requests"],3)
            self.assertEqual(result["scenes"][1]["independent_review"]["automated_result"],"FAIL")
            self.assertFalse(result["ready_to_publish"])
            self.assertFalse(result["youtube_enabled"])

    def test_dry_run_preserves_publication_gate(self):
        story = _story()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "checkpoint.json"
            planned = _plan()
            with patch.object(cp, "_read_checkpoint", return_value=(planned, 2)), \
                 patch.object(cp, "validate_plan", return_value=planned), \
                 patch.object(cp, "check_explicit_story_constraints", return_value=True):
                data = cp.pilot(story, path, Path(root) / "out", "", "", live=False)
            self.assertEqual(data["completed_image_requests"], 0)
            self.assertEqual(len(data["scenes"]), 3)
            self.assertFalse(data["ready_to_publish"])
            self.assertFalse(data["youtube_enabled"])
            self.assertTrue((Path(root) / "out" / "cinematic-pilot-manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
