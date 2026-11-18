"""Offline regression tests: no external API calls or secrets required."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.image_generation import build, image_dimensions, scene_prompts, generate_cloudflare, MAX_PROMPT


def jpeg(w=512, h=512):
    # Minimal marker stream for header parser only; not a decodable photograph.
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"
            + h.to_bytes(2, "big") + w.to_bytes(2, "big")
            + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
            + b"\xff\xd9" + b"\x00"*8)

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

    def test_jpeg_validation(self):
        self.assertEqual(image_dimensions(jpeg()), (512, 512, '.jpg'))
        with self.assertRaises(ValueError):
            image_dimensions(b'not an image')

    def test_prompts_fit_api_limit(self):
        doc={'scenes':[{'image_prompt':'cosmic star '*400}]}
        self.assertLessEqual(len(scene_prompts(doc)[0]['prompt']),MAX_PROMPT)

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
