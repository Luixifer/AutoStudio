"""Regression: transparent QC diagnostics without approving rejected visual art."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from scripts import visual_autopilot as a

def jpeg():
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"+(512).to_bytes(2,"big")*2+
            b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"+b"\xff\xd9"+b"\x00"*8)

class DiagnosticsTests(unittest.TestCase):
    def test_unapproved_image_logs_vision_reason_and_does_not_approve(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"story.json"
            p.write_text(json.dumps({"title":"Test","scenes":[{"narration":"A gas giant is orbiting close to its bright star."}]}))
            sink=io.StringIO()
            with patch.dict("os.environ",{"CLOUDFLARE_ACCOUNT_ID":"a"*32,"CLOUDFLARE_API_TOKEN":"SECRET_TOKEN"}):
                with redirect_stdout(sink):
                    r=a.run(p,Path(t)/"out",live=True,
                       director=lambda *args:"A photorealistic gas giant orbiting next to a large luminous star.",
                       generator=lambda *args:jpeg(),
                       vision=lambda *args:{"decision":"FAIL","evidence":"Solid mountains appear where a gas atmosphere belongs."},
                       request_budget=1)
            self.assertFalse(r["all_scenes_approved"])
            self.assertIn("Solid mountains appear",sink.getvalue())
            self.assertNotIn("SECRET_TOKEN",sink.getvalue())
            self.assertEqual(r["scenes"][0]["status"],"needs_human_review")

if __name__=="__main__":
    unittest.main()
