import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.image_duplicate_qa import audit, fingerprint

class ImageDuplicateQATests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def image(self, name, pattern):
        path = self.root / name
        image = Image.new("RGB", (160, 128), (10, 10, 10))
        painter = ImageDraw.Draw(image)
        if pattern == "left":
            painter.rectangle((3, 3, 75, 125), fill=(250, 250, 250))
        elif pattern == "right":
            painter.rectangle((84, 3, 155, 125), fill=(250, 250, 250))
        else:
            painter.rectangle((3, 3, 155, 55), fill=(250, 250, 250))
        image.save(path)
        return path

    def test_byte_identical_images_block(self):
        a = self.image("a.png", "left")
        b = self.root / "b.png"
        b.write_bytes(a.read_bytes())
        result = audit([a, b])
        self.assertEqual(result["pairs"][0]["verdict"], "DUPLICATE")
        self.assertFalse(result["ready_to_publish"])
        self.assertFalse(result["editorial_approved"])

    def test_reencoded_same_scene_flagged(self):
        a = self.image("a.png", "left")
        b = self.image("b.webp", "left")
        result = audit([a, b])
        self.assertEqual(result["pairs"][0]["verdict"], "POSSIBLE_DUPLICATE")
        self.assertFalse(result["scientific_facts_verified"])

    def test_distinct_scene_no_false_approval(self):
        a = self.image("a.png", "left")
        b = self.image("b.png", "right")
        report = audit([a, b])
        self.assertEqual(report["pairs"][0]["verdict"], "DISTINCT_BY_HASH")
        self.assertFalse(report["ready_to_publish"])

    def test_reject_malformed_inputs(self):
        a = self.image("a.png", "left")
        with self.assertRaises(ValueError):
            audit([a, a])
        with self.assertRaises(ValueError):
            fingerprint(self.root / "missing.png")

if __name__ == "__main__":
    unittest.main()
