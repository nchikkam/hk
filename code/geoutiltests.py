import unittest
from lib.geoutils import (
    distance,
    bearing,
    midPoint,
    destinationPoint
)

class GeoUtilTest(unittest.TestCase):

    def testDistance(self):
        d = distance(52.5318, 13.3898, 52.52346, 13.35981)
        self.assertEqual(2.23068722752817, d)

        # seattle = [47.621800, -122.350326]
        # olympia = [47.041917, -122.893766]
        d = distance(47.621800, -122.350326, 47.041917, -122.893766)
        self.assertEqual(76.3866157995487, d)

    def testBearing(self):

        self.assertAlmostEqual(250.20613449040263, bearing(43.682213, -70.450696, 43.682194, -70.450769))
        self.assertAlmostEqual(0.0, bearing(0.0,0.0,0.0,0.0))
        self.assertAlmostEqual(90.0, bearing(0.0,0.0,0.0,10.0))
        self.assertAlmostEqual(0.0, bearing(0.0,0.0,10.0,0.0))
        self.assertAlmostEqual(270.0, bearing(0.0,0.0,0.0,-10.0))
        self.assertAlmostEqual(180.0, bearing(0.0,0.0,-10.0,0.0))
        self.assertAlmostEqual(95.7108811674, bearing(0.0,0.0,-1.0,10.0))
        self.assertAlmostEqual(96.1925793306, bearing(53.32055555555556 , -1.7297222222222221, 53.31861111111111, -1.6997222222222223))
        self.assertAlmostEqual(96.1925793306, bearing(53.32055555555556 , -1.7297222222222221, 53.31861111111111, -1.6997222222222223))
        self.assertAlmostEqual(96.1785339844, bearing(53.32055, -1.72972, 53.31861, -1.69972))


    def testMidPoint(self):

        (lat, lon) = midPoint(43.682213, -70.450696, 43.682194, -70.450769)

        self.assertAlmostEqual(lat, 43.6822035)
        self.assertAlmostEqual(lon, -70.45069663704528)

    def testDestinationPoint(self):

        (lat, lon) = destinationPoint(43.682213, -70.450696, 6, 10)
        self.assertAlmostEqual(lat, 43.68253199443845)
        self.assertAlmostEqual(lon, -70.27616336631444)


if __name__ == "__main__":
    unittest.main()