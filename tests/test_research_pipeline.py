"""Offline integration tests: producing a research dossier is not producing a video."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.research_pipeline import prepare_research_package, write_package
from scripts.topic_intake import prepare_topic


class ResearchPipelineTests(unittest.TestCase):
    def test_new_topic_produces_unapproved_storyboard_without_media(self):
        def fake_research(topic):
            result = prepare_topic(topic)
            result["research"] = {"status": "leads_found_not_verified"}
            result["sources"] = [{
                "title": "Bibliografía preliminar",
                "url": "https://es.wikipedia.org/wiki/Luna",
                "evidence_level": "secondary_lead_only",
            }]
            return result

        result = prepare_research_package("¿Por qué vemos siempre la misma cara de la Luna?", fake_research)
        self.assertEqual(result["state"], "editorial_review_required")
        self.assertFalse(result["safe_for_render"])
        self.assertFalse(result["paid_api_allowed"])
        self.assertFalse(result["youtube_enabled"])
        self.assertEqual(len(result["storyboard"]["scenes"]), 6)
        for scene in result["storyboard"]["scenes"]:
            self.assertIsNone(scene["narration"])
            self.assertIsNone(scene["visual_asset"])

    def test_known_catalog_is_not_rewritten(self):
        result = prepare_research_package(
            "Auroras polares",
            lambda topic: dict(prepare_topic(topic), research={"status": "already_curated"}),
        )
        self.assertEqual(result["state"], "existing_catalog")
        self.assertTrue(result["safe_for_render"])
        self.assertEqual(result["existing_topic_id"], "auroras")

    def test_unavailable_research_does_not_claim_success(self):
        def offline(topic):
            return dict(prepare_topic(topic), research={"status": "unavailable"})
        result = prepare_research_package("Materia oscura", offline)
        self.assertEqual(result["state"], "research_unavailable")
        self.assertFalse(result["safe_for_render"])

    def test_persistence_and_filename_injection_guard(self):
        result = prepare_research_package("¿Qué es la gravedad?", lambda t: dict(
            prepare_topic(t), research={"status": "no_leads"}
        ))
        with tempfile.TemporaryDirectory() as directory:
            file = write_package(result, directory)
            self.assertTrue(file.is_file())
            stored = json.loads(file.read_text(encoding="utf-8"))
            self.assertEqual(stored["topic"], result["topic"])
            self.assertEqual(file.parent, Path(directory))
            self.assertFalse((Path(directory) / (result["key"] + ".partial")).exists())
            with self.assertRaises(ValueError):
                write_package(dict(result, key="../escape"), directory)


if __name__ == "__main__":
    unittest.main()
