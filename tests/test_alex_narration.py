"""Keep the user's chosen Alex voice for all personal narration previews."""
import unittest
from scripts.neural_narration import (
    DEFAULT_VOICE, DEFAULT_SPEED, DEFAULT_SENTENCE_PAUSE, DEFAULT_CLAUSE_PAUSE
)
from scripts.kelt9b_voice_comparison import PRESETS, SAMPLE_TEXT

class AlexNarratorPreferenceTests(unittest.TestCase):
    def test_narrator_default_is_selected_voice(self):
        self.assertEqual(DEFAULT_VOICE,"em_alex")
        self.assertGreaterEqual(DEFAULT_SPEED,.9)
        self.assertLessEqual(DEFAULT_SPEED,1.1)
        self.assertLessEqual(DEFAULT_SENTENCE_PAUSE,.4)
        self.assertLessEqual(DEFAULT_CLAUSE_PAUSE,.2)

    def test_comparison_keeps_script_identical_and_varies_only_pacing(self):
        self.assertEqual(len(PRESETS),3)
        self.assertTrue(all(voice=="em_alex" for _,voice,*_ in PRESETS))
        self.assertEqual(len(set(label for label,*_ in PRESETS)),3)
        self.assertEqual(len(set(speed for _,_,speed,*_ in PRESETS)),3)
        self.assertIn("KELT nueve be", SAMPLE_TEXT)
        self.assertIn("hidrógeno", SAMPLE_TEXT)

if __name__=="__main__":
    unittest.main()
