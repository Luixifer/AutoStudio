"""A/B comparison must never grant production approval or spend 2 images."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts import compare_visual_models as cmp
from tests.test_vision_gemma import jpeg


class ComparisonTests(unittest.TestCase):
    def create_source(self, directory):
        data=jpeg()
        (directory / "scene.jpg").write_bytes(data)
        (directory / "orbit-qa.json").write_text(json.dumps({
            "scene": 8, "image_generated": True,
            "file": "scene.jpg",
            "prompt": "A bright host star clearly distinguishable from the gaseous exoplanet.",
            "dimensions": [512,512],
            "sha256": hashlib.sha256(data).hexdigest()}))

    def test_generates_exactly_one_and_never_approves(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.create_source(root)
            calls=[]
            def fake_image(*_args):
                calls.append("image")
                return jpeg()
            def fake_gemma(*_args):
                return {"decision":"PASS","evidence":"Looks good"}
            def fake_scout(*_args):
                return {"decision":"FAIL","evidence":"Both spheres resemble planets"}
            result=cmp.compare(root, root/"result", "Gas giant orbits its parent star",
                               "account","token",live=True,generator=fake_image,
                               gemma=fake_gemma,scout=fake_scout)
            self.assertEqual(calls,["image"])
            self.assertEqual(result["new_image_requests_attempted"],1)
            self.assertEqual(len(result["results"]),2)
            for entry in result["results"]:
                self.assertEqual(entry["inspection"]["automated_result"],"FAIL")
                self.assertFalse(entry["inspection"]["ready_to_publish"])
            self.assertFalse(result["ready_to_publish"])

    def test_tampered_reference_blocks_before_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.create_source(root)
            (root/"scene.jpg").write_bytes(jpeg()+b"tamper")
            calls=[]
            with self.assertRaises(ValueError):
                cmp.compare(root,root/"output","Gas giant orbits star",
                            "account","token",live=True,
                            generator=lambda *_: calls.append(1))
            self.assertEqual(calls,[])

    def test_dry_run_does_not_use_paid_models(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.create_source(root)
            result=cmp.compare(root,root/"output","Gas giant orbits star",
                               "","",live=False,
                               generator=lambda *_: self.fail("No external requests"))
            self.assertEqual(result["new_image_requests_attempted"],0)
            self.assertEqual(len(result["results"]),1)


if __name__ == "__main__":
    unittest.main()
