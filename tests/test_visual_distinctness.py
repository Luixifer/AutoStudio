"""Cross-scene image-based description similarity: offline safety regressions."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.visual_distinctness import compare_visual_evidence,visual_terms
from scripts import visual_autopilot as auto

def jpeg():
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"
        + (512).to_bytes(2,"big")*2
        + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
        + b"\xff\xd9"+b"\x00"*8)

FIRST = ("The image shows a swirling vortex of orange and yellow gas against "
         "a black background with a bright central light source and turbulent strands.")
SIMILAR = ("The image depicts swirling vortex gas strands with a central light "
           "source and turbulent motion in dark space.")
DISTINCT = ("The image shows a wide side-on planet disk beside a distant stellar "
            "companion, with curved orbit lines and a star at left.")

class VisualDistinctnessTests(unittest.TestCase):
    def test_generic_colors_do_not_hide_duplicate_structure(self):
        found=compare_visual_evidence(SIMILAR,[(1,FIRST)])
        self.assertIsNotNone(found)
        self.assertEqual(found["prior_scene"],1)
        self.assertGreaterEqual(found["score"],.68)

    def test_different_composition_same_subject_is_allowed(self):
        self.assertIsNone(compare_visual_evidence(DISTINCT,[(1,FIRST)]))

    def test_too_short_observation_is_not_fake_evidence_of_duplicates(self):
        self.assertIsNone(compare_visual_evidence("Gas near star.",[(1,FIRST)]))
        self.assertNotIn("orange",visual_terms(FIRST))

    def test_repeated_actual_vision_description_blocks_second_scene(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"story.json"
            path.write_text(json.dumps({"schema":3,"title":"Cosmos",
                "scenes":[{"narration":"A gaseous planet spins around a brilliant star."},
                          {"narration":"Stellar winds disturb a nearby gas atmosphere."}]}))
            vision_iter=iter([{"decision":"PASS","evidence":FIRST},
                              {"decision":"PASS","evidence":SIMILAR}])
            with patch.dict("os.environ",{"CLOUDFLARE_ACCOUNT_ID":"a"*32,
                         "CLOUDFLARE_API_TOKEN":"test"}):
                report=auto.run(path,Path(d)/"images",live=True,max_attempts=1,
                    request_budget=2,
                    director=lambda *args:"Scientific exterior photograph of a gas planet near star with natural lighting.",
                    generator=lambda *args:jpeg(),
                    vision=lambda *args:next(vision_iter))
            self.assertFalse(report["all_scenes_approved"])
            self.assertTrue(report["scenes"][0]["approved"])
            self.assertFalse(report["scenes"][1]["approved"])
            verdict=report["scenes"][1]["candidates"][0]["vision"]
            self.assertEqual(verdict["decision"],"FAIL")
            self.assertEqual(verdict["method"],"cross_scene_visual_distinctness")
            self.assertEqual(verdict["original_vision"]["decision"],"PASS")
            self.assertEqual(report["completed_requests"],2)

    def test_varied_observation_passes_without_second_generation(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"story.json"
            path.write_text(json.dumps({"schema":3,"scenes":[
                {"narration":"A gas planet is orbiting its luminous companion."},
                {"narration":"The gas planet is seen from afar with its stellar orbit."}]}))
            vision_iter=iter([{"decision":"PASS","evidence":FIRST},
                              {"decision":"PASS","evidence":DISTINCT}])
            with patch.dict("os.environ",{"CLOUDFLARE_ACCOUNT_ID":"a"*32,
                         "CLOUDFLARE_API_TOKEN":"test"}):
                result=auto.run(path,Path(d)/"art",live=True,max_attempts=1,
                    request_budget=2,
                    director=lambda *a:"Photorealistic cosmic gas world in space with an orbiting companion.",
                    generator=lambda *a:jpeg(),
                    vision=lambda *a:next(vision_iter))
            self.assertTrue(result["all_scenes_approved"])

if __name__=="__main__":
    unittest.main()
