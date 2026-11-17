"""Offline preview gate tests: never present a research demo as approved science."""
import unittest
from scripts.research_preview import validate_preview

Q="¿Qué ocurre dentro de un agujero negro?"
NASA="https://science.nasa.gov/universe/black-holes/anatomy/"
def pkg(topic=Q):
    return {
        "topic":topic,"safe_for_render":False,
        "spanish_draft":{"approved":False,"can_render":False,"scenes":[{
            "role":x,
            "narration_draft_es":"El horizonte de sucesos marca una frontera esencial en este relato científico provisional.",
            "reference_url":NASA,
        } for x in ("Apertura","Frontera","Límites")]}
    }

class PreviewContractTests(unittest.TestCase):
    def test_preview_is_limited_and_unapproved(self):
        self.assertEqual(len(validate_preview(pkg())),3)
        for other in ("¿Qué ocurre dentro del Sol?","¿Cómo se forman los agujeros negros?"):
            with self.assertRaises(ValueError):
                validate_preview(pkg(other))

    def test_cannot_use_approved_or_malformed_draft(self):
        data=pkg()
        data["safe_for_render"]=True
        with self.assertRaises(ValueError):validate_preview(data)
        data=pkg()
        data["spanish_draft"]["scenes"].pop()
        with self.assertRaises(ValueError):validate_preview(data)
        data=pkg()
        data["spanish_draft"]["approved"]=True
        with self.assertRaises(ValueError):validate_preview(data)

    def test_untrusted_reference_is_rejected(self):
        data=pkg()
        data["spanish_draft"]["scenes"][0]["reference_url"]="https://science.nasa.gov.evil.org/"
        with self.assertRaises(ValueError):validate_preview(data)

if __name__=="__main__":
    unittest.main()
