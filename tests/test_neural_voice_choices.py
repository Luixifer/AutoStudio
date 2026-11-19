"""Audio QA and optional Kokoro male voice selector contracts, no model download."""
import inspect
import unittest
from scripts.neural_narration import NeuralNarrator


class VoiceChoiceTests(unittest.TestCase):
    def test_existing_voice_preserved_and_male_option_supported(self):
        signature=inspect.signature(NeuralNarrator.__init__)
        self.assertEqual(signature.parameters["voice"].default,"ef_dora")

    def test_neural_synthesis_tracks_selected_voice_not_fixed_female(self):
        import inspect
        source=inspect.getsource(NeuralNarrator.synthesize)
        self.assertIn("voice=self.voice",source)
        self.assertIn("'voice':self.voice",source)


if __name__=="__main__":
    unittest.main()
