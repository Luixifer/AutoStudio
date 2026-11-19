"""Read-only retrospective visual consistency report."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.audit_visual_history import audit

VORTEX1="The image shows a swirling vortex of gas with a bright central light source and turbulent strands."
VORTEX2="The image depicts swirling vortex gas strands with a central light source and turbulent motion."
OTHER="The picture shows a wide orbital planet disk beside a distant stellar companion with curved orbit lines."

class HistoricalAuditTests(unittest.TestCase):
    def test_duplicate_approved_images_would_trigger_review(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"manifest.json"
            entries=[]
            for i,(decision,evidence) in enumerate([("PASS",VORTEX1),("PASS",VORTEX2),
                                                      ("PASS",OTHER),("UNSURE","No answer")],1):
                entries.append({"scene":i,"candidates":[{"vision":{"decision":decision,
                                                                    "evidence":evidence}}]})
            path.write_text(json.dumps({"schema":2,"scenes":entries}))
            original=path.read_bytes()
            r=audit(path)
            self.assertEqual(r["previously_individual_passed"],3)
            self.assertEqual(r["individually_rejected_or_unsure"],1)
            self.assertEqual(len(r["visual_composition_duplicates"]),1)
            self.assertEqual(r["visual_composition_duplicates"][0]["scene"],2)
            self.assertEqual(r["visual_composition_duplicates"][0]["prior_scene"],1)
            self.assertTrue(r["would_require_additional_review"])
            self.assertFalse(r["publication_approved"])
            self.assertEqual(original,path.read_bytes())

if __name__=="__main__":
    unittest.main()
