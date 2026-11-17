"""Actual FFmpeg smoke test. Uses an artificial tone, NOT human speech."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.personal_editor import produce
from test_personal_studio import make_sample

class LiveRenderTests(unittest.TestCase):
    def test_real_mp4_has_safe_manifest_and_exact_caption_coverage(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            document=make_sample(base,seconds=3.3)
            manifest=base/"studio.json"
            manifest.write_text(json.dumps(document,ensure_ascii=False),encoding="utf-8")
            output=base/"out"
            report=produce(manifest,output,allow_lab=True)
            self.assertTrue(report["technical_passed"],report["errors"])
            self.assertEqual(report["size"],[720,1280])
            self.assertEqual(len(report["shots"]),2)
            self.assertGreater(report["subtitle_words"],10)
            self.assertLess(report["seconds"],10)
            self.assertFalse(report["ready_to_publish"])
            self.assertFalse(report["youtube_enabled"])
            self.assertTrue((output/"captions.srt").is_file())
            self.assertTrue((output/"autostudio-personal-REVIEW.mp4").is_file())
            self.assertEqual(len(report["sha256"]),64)

if __name__=="__main__":
    unittest.main()
