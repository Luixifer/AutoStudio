"""Offline-only tests; no external network or factual verification claimed."""
import json
import unittest
from io import BytesIO
from unittest.mock import patch

from scripts.topic_research import fetch_wikipedia_candidates, research_topic


class Response:
    def __init__(self, payload):
        self.data = BytesIO(json.dumps(payload).encode("utf-8"))
    def read(self, count=-1):
        return self.data.read(count)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class ResearchTests(unittest.TestCase):
    def test_research_collects_leads_but_does_not_authorize_render(self):
        result = research_topic("Satélites de Júpiter", collector=lambda topic: [
            {"provider": "Wikipedia en español", "url": "https://es.wikipedia.org/wiki/J%C3%BApiter"}
        ])
        self.assertEqual(result["research"]["status"], "leads_found_not_verified")
        self.assertEqual(result["research"]["verified_scientific_sources"], 0)
        self.assertFalse(result["can_render"])
        self.assertFalse(result["scenes"])

    def test_known_topic_preserves_catalog(self):
        result = research_topic("Auroras polares", collector=lambda topic: self.fail("no call needed"))
        self.assertTrue(result["can_render"])
        self.assertEqual(result["research"]["status"], "already_curated")

    def test_no_network_or_empty_results_means_no_render(self):
        from urllib.error import URLError
        for fn in [lambda topic: [], lambda topic: (_ for _ in ()).throw(URLError("offline"))]:
            result = research_topic("El núcleo de la Tierra", collector=fn)
            self.assertFalse(result["can_render"])
            self.assertIn(result["research"]["status"], ["no_leads", "unavailable"])

    def test_provider_strips_untrusted_links_and_limits_extract(self):
        payload = {"query": {"pages": [
            {"title": "Aurora", "fullurl": "https://es.wikipedia.org/wiki/Aurora_polar",
             "extract": "a" * 30000},
            {"title": "Malicioso", "fullurl": "http://example.com/bad", "extract": "Falso"},
        ]}}
        def fake_open(request, timeout):
            self.assertEqual(timeout, 12)
            self.assertIn("es.wikipedia.org", request.full_url)
            return Response(payload)
        results = fetch_wikipedia_candidates("Aurora", opener=fake_open)
        self.assertEqual(len(results), 1)
        self.assertLessEqual(len(results[0]["excerpt"]), 12000)
        self.assertEqual(results[0]["evidence_level"], "secondary_lead_only")

    def test_inside_question_retrieves_second_targeted_query(self):
        from scripts.topic_research import focused_query
        self.assertIn("interior horizonte", focused_query("¿Qué ocurre dentro de un agujero negro?"))
        urls = []
        def fake_open(request, timeout):
            from urllib.parse import parse_qs, urlsplit
            term = parse_qs(urlsplit(request.full_url).query)["gsrsearch"][0]
            urls.append(term)
            if len(urls) == 1:
                return Response({"query": {"pages": [{
                    "title": "Agujero negro",
                    "fullurl": "https://es.wikipedia.org/wiki/Agujero_negro",
                    "extract": "Los agujeros negros son objetos astronómicos muy densos."}]}})
            return Response({"query": {"pages": [{
                "title": "Singularidad gravitacional",
                "fullurl": "https://es.wikipedia.org/wiki/Singularidad_gravitacional",
                "extract": "El interior de un agujero negro plantea preguntas sobre la singularidad gravitacional."}]}})
        results = fetch_wikipedia_candidates("¿Qué ocurre dentro de un agujero negro?", opener=fake_open)
        self.assertEqual(len(urls), 2)
        self.assertEqual(len(results), 2)
        self.assertIn("horizonte", urls[1])
        self.assertEqual(results[1]["discovery_query"], urls[1])

    def test_wikipedia_discovery_excludes_samsung_fiction_and_white_hole(self):
        payload={"query":{"pages":[
            {"title":"A Matter of Time (Stargate SG-1)",
             "fullurl":"https://es.wikipedia.org/wiki/A_Matter_of_Time_(Stargate_SG-1)",
             "extract":"La gravedad del agujero negro afecta al tiempo dentro del Comando Stargate."},
            {"title":"Agujero blanco",
             "fullurl":"https://es.wikipedia.org/wiki/Agujero_blanco",
             "extract":"El agujero blanco es el reverso temporal de un agujero negro."},
            {"title":"Horizonte de sucesos",
             "fullurl":"https://es.wikipedia.org/wiki/Horizonte_de_sucesos",
             "extract":"El horizonte de sucesos marca el límite de un agujero negro."},
        ]}}
        results=fetch_wikipedia_candidates(
            "¿Qué ocurre dentro de un agujero negro?",
            opener=lambda request,timeout: Response(payload))
        self.assertEqual([entry["title"] for entry in results], ["Horizonte de sucesos"])

    def test_response_size_limit(self):
        class HugeResponse(Response):
            def read(self, count=-1):
                return b"x" * (500_001)
        with self.assertRaisesRegex(ValueError, "demasiado grande"):
            fetch_wikipedia_candidates("Aurora", opener=lambda req, timeout: HugeResponse({}))


if __name__ == "__main__":
    unittest.main()
