"""Curated topics are explicit and require different authored visual material."""
import tempfile
import unittest
from pathlib import Path

from scripts.personal_catalog import TOPICS,create_bundle,resolve_topic

class CuratedTopicsTests(unittest.TestCase):
    def test_exact_three_supported_categories(self):
        self.assertEqual(set(TOPICS),{"auroras","dna","volcanoes"})
        self.assertEqual(resolve_topic("¿Por qué hay auroras boreales?"),"auroras")
        self.assertEqual(resolve_topic("¿Qué es el ADN?"),"dna")
        self.assertEqual(resolve_topic("¿Cómo funcionan los volcanes?"),"volcanoes")

    def test_reject_unrelated_and_ambiguous_queries(self):
        for query in ("¿Qué hay dentro de un agujero negro?",
                      "¿Cuántos planetas tiene Júpiter?",
                      "volcanes y auroras",""):
            with self.subTest(query=query):
                with self.assertRaises(ValueError):resolve_topic(query)

    def test_all_topics_have_distinct_artwork_narration_and_8_scenes(self):
        with tempfile.TemporaryDirectory() as root:
            import json
            observed_titles=set()
            all_images=set()
            for topic in TOPICS:
                path=create_bundle(topic,Path(root)/topic)
                doc=json.loads(path.read_text(encoding="utf-8"))
                self.assertFalse(doc["editorial_approved"])
                self.assertFalse(doc["youtube"]["enabled"])
                self.assertEqual(len(doc["scenes"]),8)
                self.assertNotIn(doc["title"],observed_titles)
                observed_titles.add(doc["title"])
                for s in doc["scenes"]:
                    self.assertTrue((path.parent/s["image"]).is_file())
                    self.assertGreater(len(s["narration"].split()),7)
                    self.assertEqual(s["rights"]["license"],"own_creation")
                    all_images.add(s["image"])
            self.assertEqual(len(all_images),24)

if __name__=="__main__":unittest.main()
