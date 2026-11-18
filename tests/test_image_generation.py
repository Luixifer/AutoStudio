"""Offline regression tests: no external API calls or secrets required."""
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.image_generation import build, png_dimensions, scene_prompts, generate_cloudflare

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAIAAADy5G5u")  # header only for dimension checks

class ImageGenerationTests(unittest.TestCase):
    def test_prompts_are_cinematic_and_scene_specific(self):
        p = scene_prompts({"scenes":[{"image_prompt":"A blue giant star"},{"image_prompt":"A hot gas planet"}]})
        self.assertEqual(len(p),2)
        self.assertIn("Photorealistic",p[0]["prompt"])
        self.assertIn("hot gas planet",p[1]["prompt"])
        self.assertNotIn("hot gas planet",p[0]["prompt"])

    def test_missing_visual_brief_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"explicit visual"):
            scene_prompts({"scenes":[{"voice":"a planet"}]})

    def test_png_validation(self):
        self.assertEqual(png_dimensions(PNG),(512,512))
        with self.assertRaises(ValueError):
            png_dimensions(b"not an image")

    def test_dry_run_creates_only_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            story = Path(temp)/"story.json"
            story.write_text(json.dumps({"scenes":[{"image_prompt":"A star"}]}))
            out = Path(temp)/"out"
            with patch("scripts.image_generation.generate_cloudflare",side_effect=AssertionError("network called")):
                result = build(story,out,variants=2)
            self.assertEqual(result["completed_requests"],0)
            self.assertEqual(len(list(out.iterdir())),1)
            self.assertEqual(result["planned_requests"],2)

    def test_budget_blocks_before_network(self):
        with tempfile.TemporaryDirectory() as temp:
            story = Path(temp)/"story.json"
            story.write_text(json.dumps({"scenes":[{"image_prompt":"A star"}]*10}))
            with self.assertRaisesRegex(ValueError,"budget"):
                build(story,Path(temp)/"out",variants=3,max_requests=10)

    def test_live_requires_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            story=Path(temp)/"story.json"
            story.write_text(json.dumps({"scenes":[{"image_prompt":"A star"}]}))
            with patch.dict("os.environ",{"CLOUDFLARE_ACCOUNT_ID":"","CLOUDFLARE_API_TOKEN":""}):
                with self.assertRaisesRegex(ValueError,"secrets"):
                    build(story,Path(temp)/"out",live=True)

if __name__=="__main__":
    unittest.main()
