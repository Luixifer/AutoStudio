import unittest
from scripts.procedural_molecule import molecular_centers,molecular_frame,smoothstep


class HydrogenSceneTests(unittest.TestCase):
    def test_hydrogen_separation_is_smooth_and_monotonic(self):
        d=[]
        for i in range(121):
            a,b=molecular_centers(i/120,"dissociation")
            d.append(b[0]-a[0])
        self.assertAlmostEqual(d[0],92)
        self.assertAlmostEqual(d[-1],452)
        self.assertTrue(all(b>=a for a,b in zip(d,d[1:])))
        self.assertLess(max(b-a for a,b in zip(d,d[1:])),10)

    def test_recombination_reverses_distance(self):
        for i in range(121):
            a,b=molecular_centers(i/120,"recombination")
            c,d=molecular_centers(i/120,"dissociation")
            self.assertAlmostEqual((b[0]-a[0])+(d[0]-c[0]),544)

    def test_frame_is_actual_rendered_rgb(self):
        first=molecular_frame(0,120,"dissociation")
        last=molecular_frame(100,120,"dissociation")
        self.assertEqual(first.size,(1280,720))
        self.assertNotEqual(first.tobytes(),last.tobytes())

    def test_only_two_valid_modes(self):
        with self.assertRaises(ValueError):
            molecular_centers(.5,"ionization")
        with self.assertRaises(ValueError):
            smoothstep(1.2)
