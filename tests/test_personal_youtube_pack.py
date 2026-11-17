"""Manual YouTube export must never invent verification or auto-publish."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.personal_youtube_pack import produce_upload_pack,validate_metadata

class YouTubePackTests(unittest.TestCase):
    def test_short_package_is_manual_and_has_no_revenue_promise(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            manifest={"title":"Las auroras y el universo","format":"short",
                      "scenes":[{"narration":"El cielo brilla con luces de colores."},
                                {"narration":"El campo magnético influye sobre las partículas."}]}
            quality={"technical_passed":True,"ready_to_publish":False,
                     "video":str(p/"not-available.mp4"),"sha256":"a"*64,
                     "shots":[{"seconds":5},{"seconds":5}],"warnings":[]}
            (p/"manifest.json").write_text(json.dumps(manifest))
            (p/"quality.json").write_text(json.dumps(quality))
            result=produce_upload_pack(p/"manifest.json",p/"quality.json",p/"publish")
            self.assertFalse(result["youtube_published"])
            self.assertIsNone(result["revenue_estimate"])
            self.assertTrue(result["synthetic_visual_disclosure_review_required"])
            self.assertIn("Fuentes científicas pendientes",result["description"])
            self.assertTrue((p/"publish/youtube-draft.txt").is_file())

    def test_documentary_chapters_are_derived_from_actual_timeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            manifest={"title":"Documental de los misterios del cosmos","format":"documentary",
                "scenes":[{"heading":f"Capítulo {i+1}",
                           "narration":"Un detalle fascinante del cosmos."} for i in range(8)]}
            quality={"technical_passed":True,"ready_to_publish":False,
                "video":str(p/"missing.mp4"),"sha256":"b"*64,
                "shots":[{"seconds":75} for _ in range(8)],"warnings":[]}
            (p/"manifest.json").write_text(json.dumps(manifest))
            (p/"quality.json").write_text(json.dumps(quality))
            result=produce_upload_pack(p/"manifest.json",p/"quality.json",p/"publish")
            self.assertEqual(len(result["chapters_suggestions"]),8)
            self.assertTrue(result["chapters_suggestions"][0].startswith("00:00:00"))
            self.assertTrue(result["chapters_suggestions"][1].startswith("00:01:15"))

    def test_no_pack_from_failed_or_published_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/"m.json").write_text(json.dumps({"title":"Un vídeo"}))
            (p/"q.json").write_text(json.dumps({"technical_passed":False}))
            with self.assertRaises(ValueError):
                produce_upload_pack(p/"m.json",p/"q.json",p/"pub")

if __name__=="__main__":unittest.main()
