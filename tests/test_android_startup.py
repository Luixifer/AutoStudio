"""Regression for the observed CI exit 127 and split AVD directories."""
import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from android.start_emulator import toolchain,main
ROOT=Path(__file__).resolve().parents[1]
class AndroidStartupTests(unittest.TestCase):
    def test_sdk_commands_do_not_depend_on_path(self):
        with tempfile.TemporaryDirectory() as d:
            env,tools,base,avds=toolchain({'ANDROID_HOME':d+'/sdk','RUNNER_TEMP':d,'PATH':'/usr/bin'})
            self.assertEqual(tools['adb'],Path(d+'/sdk/platform-tools/adb'));self.assertEqual(tools['emulator'],Path(d+'/sdk/emulator/emulator'))
            self.assertTrue(all(p.is_absolute() for p in tools.values()))
    def test_all_avd_consumers_use_the_same_explicit_home(self):
        with tempfile.TemporaryDirectory() as d:
            env,tools,base,avds=toolchain({'ANDROID_HOME':d+'/sdk','RUNNER_TEMP':d})
            self.assertEqual(env['ANDROID_AVD_HOME'],str(base/'avd'));self.assertEqual(env['ANDROID_EMULATOR_HOME'],str(base));self.assertEqual(env['ANDROID_USER_HOME'],str(base))
    def test_requested_avd_home_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            source={'ANDROID_HOME':d+'/sdk','RUNNER_TEMP':d,'ANDROID_AVD_HOME':d+'/isolated-avds','ANDROID_USER_HOME':d+'/user'}
            env,tools,base,avds=toolchain(source);self.assertEqual(avds,Path(d+'/isolated-avds'));self.assertNotIn('ANDROID_EMULATOR_HOME',source)
    def test_missing_sdk_fails_explicitly_before_spawning(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'ANDROID_HOME':d+'/missing-sdk','RUNNER_TEMP':d},clear=True),patch('android.start_emulator.subprocess.run') as run:
            with self.assertRaisesRegex(RuntimeError,'Missing official SDK executable: adb'):main()
            run.assert_not_called()
    def test_workflow_exports_platform_tools_for_instrumentation(self):
        text=(ROOT/'.github/workflows/android-lab.yml').read_text();self.assertIn('echo "$ANDROID_HOME/platform-tools" >> "$GITHUB_PATH"',text);self.assertIn('python android/start_emulator.py',text)
if __name__=='__main__':unittest.main()
