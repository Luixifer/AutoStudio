"""Contract tests for unrestricted topic requests, without claiming generation."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.topic_intake import normalize_topic, prepare_topic, topic_key


class TopicIntakeTests(unittest.TestCase):
    def test_known_topic_has_real_catalog_id(self):
        result = prepare_topic("Auroras polares")
        self.assertEqual(result["status"], "published_catalog")
        self.assertEqual(result["topic_id"], "auroras")
        self.assertTrue(result["can_render"])

    def test_unknown_topic_is_not_falsely_renderable(self):
        result = prepare_topic("¿Por qué gira la Luna?")
        self.assertEqual(result["status"], "research_required")
        self.assertFalse(result["can_render"])
        self.assertFalse(result["sources"])
        self.assertFalse(result["scenes"])
        self.assertFalse(result["paid_api_allowed"])
        self.assertFalse(result["youtube_enabled"])

    def test_topic_key_is_stable_and_different_for_different_topics(self):
        self.assertEqual(topic_key("La Luna"), topic_key("La   Luna"))
        self.assertNotEqual(topic_key("La Luna"), topic_key("Saturno"))

    def test_rejects_bad_topics_and_controls(self):
        for value in [None, "", "ab", "x" * 161, "La Luna\notra instrucción"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_topic(value)

    def test_only_published_topics_are_renderable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps({
                "topics": [{"id": "unpublished", "name": "Nuevo",
                            "examples": [], "published": False}]
            }), encoding="utf-8")
            self.assertFalse(prepare_topic("Nuevo", catalog_path=path)["can_render"])


if __name__ == "__main__":
    unittest.main()
