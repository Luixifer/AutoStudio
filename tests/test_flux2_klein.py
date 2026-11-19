"""Offline multipart and safety tests for the landscape image model."""
import unittest
from scripts import flux2_klein


class Klein4BTests(unittest.TestCase):
    def test_multipart_content_has_three_supported_fields(self):
        body, content_type = flux2_klein.build_form(
            "A large gaseous planet close to its luminous star.",
            boundary="AutoStudio123456")
        self.assertEqual(content_type,
                         "multipart/form-data; boundary=AutoStudio123456")
        self.assertIn(b'name="prompt"', body)
        self.assertIn(b'name="width"\r\n\r\n1536', body)
        self.assertIn(b'name="height"\r\n\r\n864', body)
        self.assertNotIn(b"token", body.lower())

    def test_rejects_invalid_prompt_and_unbounded_dimensions(self):
        with self.assertRaises(ValueError):
            flux2_klein.build_form("")
        with self.assertRaises(ValueError):
            flux2_klein.build_form("Photorealistic gaseous world", 1920, 1920)
        with self.assertRaises(ValueError):
            flux2_klein.generate_klein("Photorealistic gas planet", "not-an-account", "token")


if __name__ == "__main__":
    unittest.main()
