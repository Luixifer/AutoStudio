"""Gemma 4 visual QA contract — all tests offline; never consume Workers AI quota."""
import base64
import json
import unittest
from unittest.mock import patch
from scripts import vision_gemma

def jpeg():
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"+(512).to_bytes(2,"big")*2+
            b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"+b"\xff\xd9"+b"\x00"*8)

class GemmaVisionTests(unittest.TestCase):
    def test_actual_image_is_sent_to_vision_model(self):
        with patch.object(vision_gemma,"_request",
                return_value={"response":"DECISION: PASS\nEVIDENCE: A gaseous planet is visible next to a star."}) as r:
            verdict=vision_gemma.evaluate_gemma(jpeg(),"An orbiting gas giant.",
                "A glowing gaseous planet near its star.","a"*32,"tok")
        self.assertEqual(verdict["decision"],"PASS")
        args=r.call_args.args
        self.assertEqual(args[0],vision_gemma.GEMMA_VISION_MODEL)
        parts=args[1]["messages"][0]["content"]
        self.assertEqual(parts[1]["type"],"image_url")
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(base64.b64decode(parts[1]["image_url"]["url"].split(",",1)[1]),jpeg())

    def test_missing_decision_is_unapproved(self):
        for answer in ["", "Looks fantastic!", "DECISION: PASS", "DECISION: MAYBE\nEVIDENCE: Unknown"]:
            result=vision_gemma._parse_verdict(answer)
            self.assertEqual(result["decision"],"UNSURE")

    def test_explicit_fail_is_rejected(self):
        r=vision_gemma._parse_verdict("DECISION: FAIL\nEVIDENCE: Rocky mountains inconsistent with a gas giant.")
        self.assertEqual(r["decision"],"FAIL")
        self.assertIn("mountains",r["evidence"])

    def test_missing_model_output_remains_unsure(self):
        with patch.object(vision_gemma,"_request",return_value={"usage":{"tokens":2}}):
            r=vision_gemma.evaluate_gemma(jpeg(),"A gas giant","Planet in space","a"*32,"tok")
        self.assertEqual(r["decision"],"UNSURE")
        self.assertEqual(r["response_keys"],["usage"])

if __name__=="__main__":
    unittest.main()
