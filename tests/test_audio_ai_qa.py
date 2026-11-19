"""Tests with real WAV input but stub AI outputs; no downloads or paid APIs."""
import math
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from scripts import audio_ai_qa as audio


def write_clip(path, seconds=2):
    rate=16000
    samples=bytearray()
    for i in range(round(seconds*rate)):
        sample=int(8000*math.sin(2*math.pi*230*i/rate))
        samples.extend(sample.to_bytes(2,"little",signed=True))
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
        f.writeframes(samples)


class AudioQualityTests(unittest.TestCase):
    def test_spanish_accents_and_case_are_normalized(self):
        self.assertEqual(audio.word_accuracy(
            "KELT nueve bé, ¡qué extraño!", "kelt nueve be que extrano"),1.0)

    def test_recognizes_good_audio_but_never_publishes(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav=Path(tmp)/"audio.wav";write_clip(wav)
            result=audio.assess(
                wav,"El planeta está muy caliente.",
                transcription="El planeta está muy caliente.",
                speech_segments=[{"start":.2,"end":1.7}])
            self.assertEqual(result["word_match_ratio"],1.0)
            self.assertFalse(result["review_needed"])
            self.assertFalse(result["ready_to_publish"])
            self.assertFalse(result["voice_quality_approved"])
            self.assertEqual(result["engines"]["speech_detection"],
                             "Silero VAD ONNX CPU")

    def test_wrong_words_and_excessive_silence_require_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav=Path(tmp)/"audio.wav";write_clip(wav,4)
            result=audio.assess(
                wav,"La órbita dura solo treinta y seis horas.",
                transcription="No entiendo la frase",
                speech_segments=[{"start":1.4,"end":2.0}])
            self.assertTrue(result["review_needed"])
            self.assertGreaterEqual(len(result["warnings"]),2)

    def test_rejects_invalid_segments_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav=Path(tmp)/"audio.wav";write_clip(wav)
            with self.assertRaisesRegex(ValueError,"Invalid VAD"):
                audio.assess(wav,"KELT nueve be es un planeta.",
                             transcription="KELT nueve be es un planeta.",
                             speech_segments=[{"start":0,"end":22}])

    def test_rejects_missing_file(self):
        with self.assertRaises(ValueError):
            audio.pcm16("/missing/sample.wav")


if __name__=="__main__":
    unittest.main()
