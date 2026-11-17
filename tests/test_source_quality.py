"""Regression from the physical Samsung: no science narration from Stargate or white holes."""
import unittest
from scripts.source_quality import valid_science_lead
from scripts.narration_candidates import narration_candidates

class ScientificSourceQualityTests(unittest.TestCase):
    QUESTION="¿Qué ocurre dentro de un agujero negro?"

    def test_rejects_exact_samsung_fiction_source(self):
        self.assertFalse(valid_science_lead(
            self.QUESTION, "A Matter of Time (Stargate SG-1)",
            "Pronto, la fuerza de gravedad del agujero comienza a afectar la forma en que pasa el tiempo dentro del Comando Stargate."))

    def test_rejects_white_hole_speculation_as_black_hole_interior(self):
        self.assertFalse(valid_science_lead(
            self.QUESTION, "Agujero blanco",
            "Por ello se define un agujero blanco como el reverso temporal de un agujero negro: el agujero negro absorbe a su interior a la materia."))

    def test_keeps_genuine_topic_specific_candidate(self):
        self.assertTrue(valid_science_lead(
            self.QUESTION, "Horizonte de sucesos",
            "El horizonte de sucesos marca el límite de un agujero negro, según la teoría de la relatividad general."))

    def test_quarantines_entire_source_before_quote_selection(self):
        dossier={"topic":self.QUESTION,"sources":[
            {"title":"A Matter of Time (Stargate SG-1)",
             "url":"https://es.wikipedia.org/wiki/A_Matter_of_Time_(Stargate_SG-1)",
             "excerpt":"Pronto, la fuerza de gravedad del agujero comienza a afectar la forma en que pasa el tiempo dentro del Comando Stargate.",
             "evidence_level":"secondary_lead_only"},
            {"title":"Agujero blanco","url":"https://es.wikipedia.org/wiki/Agujero_blanco",
             "excerpt":"Por ello se define un agujero blanco como el reverso temporal de un agujero negro: el agujero negro absorbe a su interior a la materia.",
             "evidence_level":"secondary_lead_only"},
        ]}
        result=narration_candidates(dossier)
        self.assertEqual(result["candidates"],[])
        self.assertFalse(result["can_render"])

    def test_does_not_block_unrelated_general_science_question(self):
        self.assertTrue(valid_science_lead("¿Qué es el ADN?", "ADN",
                                           "El ADN es la molécula de la herencia genética."))

if __name__=="__main__":unittest.main()
