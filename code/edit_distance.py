import unittest
from lib.dp import (
    cost
)


class TesStringEditDistance(unittest.TestCase):

    def otestEditDistanceForZero(self):
        self.assertEqual(cost("NOTHING", "NOTHING"), 0)

    def utestEditDistanceForOne(self):
        self.assertEqual(cost("ISLANDER", "SLANDER"), 1)

    def testEditDistances(self):

        data = [ # String-A   String-B  ExpectedDistance
                 #("NOTHING",  "NOTHING", 0),
                 #("ISLANDER", "SLANDER", 1),
                 #("MART", "KARMA", 5),
                 #("KITTEN", "SITTING", 3),
                 #("INTENTION", "EXECUTION", 8),
                 ("aabab", "babb", 3),
                 #("atcat", "attatc", 3)
                ]

        for (a, b, expected) in data:
            self.assertEqual(cost(a, b), expected)

if __name__ == "__main__":
    unittest.main()