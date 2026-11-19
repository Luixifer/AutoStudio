import unittest
from scripts.procedural_orbit import orbital_position, frame_at


class OrbitEngineTests(unittest.TestCase):
    def test_closed_smooth_orbit_and_no_discontinuity(self):
        center=(640,360)
        start=orbital_position(0,center,320,180)
        end=orbital_position(1,center,320,180)
        self.assertAlmostEqual(start[0],end[0],places=8)
        self.assertAlmostEqual(start[1],end[1],places=8)
        for n in range(120):
            x,y=orbital_position(n/120,center,320,180)
            xx,yy=orbital_position((n+1)/120,center,320,180)
            self.assertLess(((x-xx)**2+(y-yy)**2)**.5,21)

    def test_frame_is_real_rgb_and_changes_with_time(self):
        a=frame_at(0,120,width=320,height=180)
        b=frame_at(30,120,width=320,height=180)
        self.assertEqual(a.mode,"RGB")
        self.assertEqual(a.size,(320,180))
        self.assertNotEqual(a.tobytes(),b.tobytes())

    def test_invalid_orbit_times_rejected(self):
        for value in (-.01,1.01):
            with self.assertRaises(ValueError):
                orbital_position(value,(0,0),10,5)
        with self.assertRaises(ValueError):
            frame_at(5,5)
