import tempfile,unittest
from pathlib import Path
from scripts.personal_editor import write_ass,ass_time
class BurnedSubtitleTests(unittest.TestCase):
 def test_short_hold_does_not_overlap_next_group(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'captions.ass';write_ass(p,[{'start':0,'end':1,'text':'Uno'},{'start':1.01,'end':2,'text':'Dos'}],(1920,1080),'Prueba',2)
   events=[line.split(',',9) for line in p.read_text().splitlines() if line.startswith('Dialogue: 2')]
   self.assertEqual(events[0][2],'0:00:01.01');self.assertEqual(events[1][2],'0:00:02.00')
 def test_centisecond_carries_to_next_minute(self):self.assertEqual(ass_time(59.999),'0:01:00.00')
