"""Narration candidates must be real short source quotations, never claimed approved."""
import unittest
from scripts.narration_candidates import narration_candidates

def source(title, excerpt):
    return {
        "title": title, "url": "https://es.wikipedia.org/wiki/" + title,
        "evidence_level": "secondary_lead_only", "excerpt": excerpt,
    }

class NarrationCandidatesTests(unittest.TestCase):
    def test_derived_words_are_exact_not_generated(self):
        sentence_a = "Un agujero negro es una región del espacio donde la gravedad es tan intensa que la luz no puede salir."
        sentence_b = "Las observaciones astronómicas permiten estudiar objetos compactos muy lejanos del sistema solar."
        data = {"topic": "Agujeros negros", "can_render": False,
                "sources": [source("Agujero_negro", sentence_a), source("Astronomía", sentence_b)]}
        result = narration_candidates(data)
        self.assertEqual(result["status"], "extractive_candidates_unverified")
        self.assertEqual([c["source_excerpt_exact"] for c in result["candidates"]], [sentence_a,sentence_b])
        self.assertFalse(result["can_render"])
        for item in result["candidates"]:
            self.assertFalse(item["approved"])
            self.assertFalse(item["narration_ready"])
            self.assertEqual(item["factual_verification"], "pending_independent_source")
            self.assertIn("creativecommons.org",item["license_url"])

    def test_short_or_incomplete_text_does_not_become_fabricated_script(self):
        data = {"topic": "Agujeros negros", "can_render": False, "sources": [
            source("Agujero_negro", "No está completo"),
            source("Agujero_negro", "Luz."),
        ]}
        result = narration_candidates(data)
        self.assertFalse(result["candidates"])
        self.assertEqual(result["status"], "no_usable_sentences")

    def test_unknown_provider_and_untrusted_url_rejected(self):
        bad = source("Agujero_negro", "Las observaciones astronómicas permiten estudiar objetos muy lejanos del sistema solar.")
        bad["url"] = "https://example.com/evil"
        self.assertFalse(narration_candidates({"topic":"Luna","sources":[bad]})["candidates"])

    def test_existing_catalog_unchanged(self):
        self.assertEqual(narration_candidates({"can_render":True,"sources":[]})["status"],"existing_catalog")

    def test_maximum_six_from_multiple_sources(self):
        sentence = "Muchas observaciones se utilizan para examinar cuidadosamente los fenómenos que suceden lejos de la Tierra."
        d = {"topic":"Universo", "sources":[source("Cosmos",(" ".join([sentence]*9)))]}
        self.assertLessEqual(len(narration_candidates(d)["candidates"]),6)

if __name__=="__main__":
    unittest.main()
