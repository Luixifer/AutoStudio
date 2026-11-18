"""Contract checks for visual direction pack: useful output, no fake image generation."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.personal_visual_briefs import make_visual_briefs,export_briefs,visual_subject

class VisualDirectorTests(unittest.TestCase):
    def setUp(self):
        self.board={"title":"KELT-9b: el planeta extremo","scenes":[
            {"narration":"Existe un planeta más caliente que la superficie de muchas estrellas."},
            {"narration":"Su atmósfera gaseosa es extraordinariamente caliente."},
            {"narration":"La estrella ilumina este mundo desde muy cerca."},
            {"narration":"Un año allí es extraordinariamente corto."}]}

    def test_original_file_names_distinct_cinematic_compositions(self):
        data=make_visual_briefs(self.board)
        self.assertEqual(len(data["scenes"]),4)
        self.assertEqual([s["suggested_filename"] for s in data["scenes"]],
                         ["imagen-01.jpg","imagen-02.jpg","imagen-03.jpg","imagen-04.jpg"])
        self.assertEqual(len(set(s["shot_type"] for s in data["scenes"])),4)
        for scene in data["scenes"]:
            self.assertIn("9:16",scene["image_prompt"])
            self.assertIn("sin texto",scene["image_prompt"])
            self.assertFalse(scene["image_generated"])
            self.assertFalse(scene["scientific_facts_verified"])
            self.assertIn("marcas de agua",scene["avoid"])

    def test_scientific_linguistic_narration_not_replaced_by_fake_claims(self):
        self.assertIn("planetario",visual_subject("Un planeta extraño aparece."))
        self.assertIn("atmósfera",visual_subject("El gas llena la atmósfera."))
        self.assertIn("fenómeno",visual_subject("Un dato que nadie puede explicar."))
        data=make_visual_briefs(self.board)
        self.assertEqual(data["scenes"][3]["narration"],self.board["scenes"][3]["narration"])

    def test_briefs_are_exported_as_editable_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/"storyboard.json"
            source.write_text(json.dumps(self.board),encoding="utf-8")
            result=export_briefs(source,root/"out")
            exported=json.loads((root/"out/direccion-visual.json").read_text())
            markdown=(root/"out/prompts-imagenes.md").read_text()
            self.assertEqual(result,exported)
            self.assertIn("imagen-04.jpg",markdown)
            self.assertIn("No genera imágenes",markdown)

    def test_invalid_inputs_fail_safely(self):
        for doc in ({"title":"a","scenes":[]}, {"title":"a","scenes":[{},{}]},
                    {"title":"a","scenes":[{"narration":"a"*601},{"narration":"b"}]}):
            with self.assertRaises(ValueError):
                make_visual_briefs(doc)

if __name__=="__main__":
    unittest.main()
