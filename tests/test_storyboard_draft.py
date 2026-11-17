"""Checks that generated editorial outlines never impersonate completed videos."""
import unittest

from scripts.storyboard_draft import draft_storyboard


class StoryboardDraftTests(unittest.TestCase):
    def test_unknown_topic_is_review_only(self):
        dossier = {
            "topic": "¿Por qué gira la Luna?",
            "can_render": False,
            "sources": [{
                "title": "Candidato",
                "url": "https://es.wikipedia.org/wiki/Luna",
                "evidence_level": "secondary_lead_only",
            }],
        }
        outline = draft_storyboard(dossier)
        self.assertEqual(outline["status"], "editorial_draft")
        self.assertEqual(len(outline["scenes"]), 6)
        self.assertFalse(outline["can_render"])
        self.assertTrue(outline["human_review_required"])
        self.assertFalse(outline["youtube_enabled"])
        self.assertEqual(outline["sources_verified"], 0)
        for scene in outline["scenes"]:
            self.assertIsNone(scene["narration"])
            self.assertIsNone(scene["visual_asset"])
            self.assertEqual(scene["verified_claims"], [])
            self.assertFalse(scene["approved"])
            self.assertEqual(scene["candidate_references"][0]["evidence_level"], "secondary_lead_only")

    def test_zero_sources_do_not_invent_citations(self):
        outline = draft_storyboard({"topic": "Una pregunta", "can_render": False, "sources": []})
        self.assertEqual(outline["source_count"], 0)
        self.assertTrue(all(not scene["candidate_references"] for scene in outline["scenes"]))
        self.assertFalse(outline["can_render"])

    def test_curated_topic_is_not_overwritten_by_draft(self):
        result = draft_storyboard({"topic": "Auroras polares", "can_render": True})
        self.assertEqual(result["status"], "already_curated")
        self.assertTrue(result["can_render"])
        self.assertFalse(result["scenes"])

    def test_malformed_dossiers_fail(self):
        for dossier in [None, {}, {"topic": "Luna", "sources": "no-es-lista"}]:
            with self.subTest(dossier=dossier), self.assertRaises(ValueError):
                draft_storyboard(dossier)


if __name__ == "__main__":
    unittest.main()
