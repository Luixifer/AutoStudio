"""A Spanish draft can never be created without matching traceable evidence."""
import unittest
from scripts.spanish_draft import draft_spanish_narration

QUESTION="¿Qué ocurre dentro de un agujero negro?"

def source(text,url="https://science.nasa.gov/universe/black-holes/anatomy/"):
    return {"excerpt_original_en":text,"source_url":url,"source_title":"NASA Anatomy","content_fetched":True}

class SpanishDraftTests(unittest.TestCase):
    def test_blocks_draft_without_nasa_passages(self):
        result=draft_spanish_narration(QUESTION,{"passages":[]})
        self.assertEqual(result["status"],"insufficient_evidence")
        self.assertEqual(result["scenes"],[])
        self.assertFalse(result["can_render"])

    def test_attributed_short_spanish_draft(self):
        evidence={"passages":[
            source("This is the event horizon, the black hole boundary beyond which there is no return."),
            source("Gas can create an accretion disk around a black hole and produce light."),
            source("In current theory, relativity predicts a singularity within a black hole."),
        ]}
        result=draft_spanish_narration(QUESTION,evidence)
        self.assertGreaterEqual(len(result["scenes"]),2)
        self.assertTrue(all(s["reference_url"].startswith("https://science.nasa.gov/") for s in result["scenes"]))
        self.assertTrue(all(s["visual_asset"] is None for s in result["scenes"]))
        self.assertFalse(result["approved"])
        self.assertFalse(result["can_render"])
        self.assertGreater(result["word_count"],15)

    def test_rejects_unread_or_untrusted_sources(self):
        bad=source("An event horizon is the boundary of a black hole.")
        bad["content_fetched"]=False
        self.assertFalse(draft_spanish_narration(QUESTION,{"passages":[bad]})["scenes"])
        bad["content_fetched"]=True
        bad["source_url"]="https://fake-science.nasa.gov.evil.org/"
        self.assertFalse(draft_spanish_narration(QUESTION,{"passages":[bad]})["scenes"])

    def test_does_not_invent_general_subject(self):
        result=draft_spanish_narration("¿Qué es el ADN?",{"passages":[source("event horizon black hole")]})
        self.assertEqual(result["status"],"unsupported_subject")
        self.assertFalse(result["scenes"])

if __name__=="__main__":unittest.main()
