"""Offline contract tests: NASA body text is not a finished scientific script."""
import unittest
from io import BytesIO
from scripts.nasa_reading import evidence_from_page,fetch_nasa_evidence
from scripts.external_sources import NASA_BLACK_HOLE_PAGES
from scripts.research_pipeline import prepare_research_package
from scripts.topic_intake import prepare_topic

URL=NASA_BLACK_HOLE_PAGES[0][1]
Q="¿Qué ocurre dentro de un agujero negro?"
HTML=('<html><body><header><p>Black holes newsletter header.</p></header><main>'
      '<nav><p>Black hole event horizon advertisement and newsletter.</p></nav>'
      '<article><p>The event horizon of a black hole is the boundary of no return; '
      'even light cannot escape after passing this boundary in classical general relativity.</p>'
      '<p>The singularity at the center of a black hole represents a limit of the classical '
      'theoretical description, rather than a directly observed region.</p>'
      '</article></main></body></html>')

class FakeResponse:
    def __init__(self,data,redirect=URL):
        self.data=BytesIO(data);self.target=redirect
        self.headers={"Content-Type":"text/html; charset=utf-8"}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n=-1):return self.data.read(n)
    def geturl(self):return self.target

class NasaReadingTests(unittest.TestCase):
    def test_extracts_prose_not_navigation(self):
        pieces=evidence_from_page(URL,HTML)
        self.assertEqual(len(pieces),2)
        self.assertTrue(all("newsletter" not in p for p in pieces))
        self.assertTrue(all(len(p)<=240 for p in pieces))

    def test_only_curated_urls_are_allowed(self):
        with self.assertRaises(ValueError):
            evidence_from_page("https://example.org/fake",HTML)

    def test_live_network_is_mocked_and_metadata_retained(self):
        result=fetch_nasa_evidence(Q,opener=lambda req,timeout:FakeResponse(HTML.encode()))
        self.assertTrue(result["passages"])
        self.assertTrue(all(p["source_url"].startswith("https://science.nasa.gov/") for p in result["passages"]))
        self.assertTrue(all(not p["ready_for_narration"] for p in result["passages"]))

    def test_external_redirect_is_rejected(self):
        result=fetch_nasa_evidence(Q,opener=lambda req,timeout:
                                   FakeResponse(HTML.encode(),redirect="https://example.org/"))
        self.assertFalse(result["passages"])
        self.assertEqual(len(result["errors"]),3)

    def test_reading_is_not_used_as_approved_guion(self):
        def stub_research(topic):
            d=prepare_topic(topic)
            d["research"]={"status":"leads_found_not_verified"}
            return d
        pkg=prepare_research_package(Q,researcher=stub_research,
                                     nasa_reader=lambda topic:{"status":"evidence_passages_unverified",
                                                                 "passages":[{"excerpt_original_en":"test"}],
                                                                 "errors":[]})
        self.assertFalse(pkg["safe_for_render"])
        self.assertFalse(pkg["storyboard"]["can_render"])
        self.assertEqual(len(pkg["nasa_evidence"]["passages"]),1)

if __name__=="__main__":unittest.main()
