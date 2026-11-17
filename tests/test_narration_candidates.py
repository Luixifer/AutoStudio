"""Regression: an excerpt must address the question, not just its scientific field."""
import unittest
from scripts.narration_candidates import narration_candidates, relevance

def source(title, excerpt):
    return {
        "title": title, "url": "https://es.wikipedia.org/wiki/" + title,
        "evidence_level": "secondary_lead_only", "excerpt": excerpt,
    }

class NarrationCandidatesTests(unittest.TestCase):
    def test_exact_quotes_and_provenance(self):
        sentence_a = "Un agujero negro es una región del espacio donde la gravedad es tan intensa que la luz no puede salir."
        sentence_b = "Los agujeros negros tienen un horizonte de sucesos que delimita una región de su interior."
        d = {"topic": "Agujeros negros", "can_render": False,
             "sources": [source("Agujero_negro", sentence_a), source("Agujero_negro", sentence_b)]}
        result = narration_candidates(d)
        self.assertEqual(result["status"], "extractive_candidates_unverified")
        self.assertEqual({c["source_excerpt_exact"] for c in result["candidates"]},{sentence_a,sentence_b})
        self.assertFalse(result["can_render"])
        for item in result["candidates"]:
            self.assertFalse(item["approved"])
            self.assertFalse(item["narration_ready"])
            self.assertEqual(item["factual_verification"], "pending_independent_source")
            self.assertIn("creativecommons.org",item["license_url"])

    def test_inside_black_hole_question_rejects_compact_stars_and_mass(self):
        # Based on the exact failure mode reported from a real Samsung test.
        tangential = "Un agujero negro supermasivo es un agujero negro con una masa del orden de millones de masas solares."
        compact = "Sin ninguna fuente de energía que luche contra el colapso gravitatorio, estas estrellas muertas están comprimidas al máximo."
        relevant = "El horizonte de sucesos de un agujero negro delimita su interior, del que no pueden regresar señales luminosas."
        dossier = {"topic": "¿Qué ocurre dentro de un agujero negro?", "sources": [
            source("Agujero_negro_supermasivo", tangential),
            source("Estrella_compacta", compact),
            source("Horizonte_de_sucesos", relevant),
        ]}
        r = narration_candidates(dossier)
        self.assertEqual([x["source_excerpt_exact"] for x in r["candidates"]], [relevant])
        self.assertFalse(r["can_render"])

    def test_silence_when_no_evidence_directly_addresses_question(self):
        d = {"topic": "¿Qué ocurre dentro de un agujero negro?", "sources":[
            source("Estrella_compacta", "Las estrellas compactas tienen densidades enormes y una gravedad muy intensa en sus superficies."),
            source("Agujero_negro_supermasivo", "Un agujero negro supermasivo tiene una masa de millones de masas solares."),
        ]}
        r = narration_candidates(d)
        self.assertEqual(r["status"], "no_relevant_evidence")
        self.assertEqual(r["candidates"], [])

    def test_short_or_incomplete_text_does_not_become_fabricated_script(self):
        d = {"topic": "Agujeros negros", "sources": [
            source("Agujero_negro", "No está completo"), source("Agujero_negro", "Luz."),
        ]}
        r = narration_candidates(d)
        self.assertFalse(r["candidates"])
        self.assertEqual(r["status"], "no_relevant_evidence")

    def test_untrusted_url_rejected(self):
        bad=source("Agujero_negro", "Los agujeros negros tienen un horizonte de sucesos que delimita una región del espacio.")
        bad["url"]="https://es.wikipedia.org.evil.com/wiki/Agujero_negro"
        self.assertFalse(narration_candidates({"topic":"Agujeros negros","sources":[bad]})["candidates"])

    def test_existing_catalog_unchanged(self):
        self.assertEqual(narration_candidates({"can_render":True,"sources":[]})["status"],"existing_catalog")

    def test_maximum_six_from_multiple_sources(self):
        sentence = "Los agujeros negros son objetos astronómicos que producen efectos gravitatorios medibles a grandes distancias."
        d={"topic":"Agujeros negros","sources":[source("Agujero_negro"," ".join([sentence]*9))]}
        self.assertLessEqual(len(narration_candidates(d)["candidates"]),6)

    def test_question_intent_is_not_satisfied_by_topic_only(self):
        sentence="Los agujeros negros son objetos astronómicos de gran influencia gravitatoria en el universo observable."
        self.assertIsNone(relevance("¿Qué ocurre dentro de un agujero negro?",sentence))
        self.assertIsNotNone(relevance("¿Qué son los agujeros negros?",sentence))

if __name__=="__main__":
    unittest.main()
