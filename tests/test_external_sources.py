"""Offline tests for the no-key institutional and scholarly discovery layer."""
import json
import unittest
from io import BytesIO
from urllib.error import URLError
from scripts.external_sources import agency_leads,crossref_leads,external_leads
from scripts.topic_research import research_topic

Q="¿Qué ocurre dentro de un agujero negro?"

class FakeResponse:
    def __init__(self,data):self.data=BytesIO(json.dumps(data).encode("utf-8"))
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n=-1):return self.data.read(n)

class ExternalResearchTests(unittest.TestCase):
    def test_nasa_links_are_official_and_never_claim_read_content(self):
        pages=agency_leads(Q)
        self.assertEqual(len(pages),3)
        for p in pages:
            self.assertTrue(p["url"].startswith("https://science.nasa.gov/"))
            self.assertFalse(p["content_fetched"])
            self.assertFalse(p["excerpt"])
        self.assertEqual(agency_leads("¿Qué es el ADN?"),[])

    def test_crossref_rejects_fiction_and_nonmatching_titles(self):
        sample={"message":{"items":[
            {"title":["A Matter of Time Stargate"],"DOI":"10.1000/stargate","type":"journal-article"},
            {"title":["White holes and singularities"],"DOI":"10.1000/white","type":"journal-article"},
            {"title":["Black hole event horizons and horizons"],"DOI":"10.1234/valid-paper","type":"journal-article"},
            {"title":["Star formation"],"DOI":"10.1234/irrelevant","type":"journal-article"},
            {"title":["Other black hole research"],"DOI":"javascript:evil","type":"journal-article"},
        ]}}
        def opener(req,timeout):
            self.assertEqual(timeout,12)
            self.assertIn("api.crossref.org/works",req.full_url)
            return FakeResponse(sample)
        items=crossref_leads(Q,opener=opener)
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]["url"],"https://doi.org/10.1234/valid-paper")
        self.assertFalse(items[0]["content_fetched"])
        self.assertEqual(items[0]["evidence_level"],"academic_metadata_lead_unreviewed")

    def test_crossref_outage_preserves_official_nasa_links(self):
        leads,err=external_leads(Q,crossref=lambda q:(_ for _ in ()).throw(URLError("offline")))
        self.assertEqual(err,"URLError")
        self.assertEqual(len(leads),3)

    def test_integration_distinguishes_sources_from_verified_claims(self):
        wiki={"title":"Horizonte de sucesos","url":"https://es.wikipedia.org/wiki/Horizonte_de_sucesos",
              "excerpt":"El horizonte marca el límite del agujero negro.",
              "provider":"Wikipedia en español","evidence_level":"secondary_lead_only"}
        nasa=agency_leads(Q)
        result=research_topic(Q,collector=lambda q:[wiki],
                              external_collector=lambda q:(nasa,None))
        self.assertEqual(len(result["sources"]),4)
        self.assertEqual(result["research"]["institutional_leads"],3)
        self.assertEqual(result["research"]["secondary_leads"],1)
        self.assertEqual(result["research"]["verified_scientific_sources"],0)
        self.assertFalse(result["can_render"])

if __name__=="__main__":unittest.main()
