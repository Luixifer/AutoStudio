"""Static integration contract for the research-only Android preview."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class AndroidResearchTests(unittest.TestCase):
    def test_research_screen_is_non_exported(self):
        manifest=(ROOT/"android/app/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn('ResearchActivity" android:exported="false"',manifest)

    def test_home_offers_research_without_claiming_video(self):
        home=(ROOT/"android/app/src/com/luixifer/autostudio/MainActivity.java").read_text(encoding="utf-8")
        self.assertIn("Investigar tema libre (prueba)",home)
        self.assertIn("Investigar no produce MP4.",home)

    def test_research_uses_existing_scoped_github_connection(self):
        research=(ROOT/"android/app/src/com/luixifer/autostudio/ResearchActivity.java").read_text(encoding="utf-8")
        client=(ROOT/"android/app/src/com/luixifer/autostudio/GitHubClient.java").read_text(encoding="utf-8")
        self.assertIn("CredentialStore",research)
        self.assertIn("dispatchResearch(requested)",research)
        self.assertIn('/actions/workflows/investigar-tema.yml/dispatches',client)
        self.assertNotIn("ghp_",research)
        self.assertNotIn("github_pat_",research)

if __name__=="__main__":
    unittest.main()
