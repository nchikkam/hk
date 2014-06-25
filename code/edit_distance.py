import unittest
from lib.dp import (
    cost,
    recursiveCost
)

class TesStringEditDistance(unittest.TestCase):

    def testEditDistances(self):

        data = [ # String-A   String-B  ExpectedDistance
                 ("NOTHING",  "NOTHING", 0),
                 ("ISLANDER", "SLANDER", 1),
                 ("MART", "KARMA", 3),
                 ("KITTEN", "SITTING", 3),
                 ("INTENTION", "EXECUTION", 5),
                 ("aabab", "babb", 2),
                 ("atcat", "attatc", 2)
                ]

        for (a, b, expected) in data:
            self.assertEqual(cost(a, b), expected)
            #self.assertEqual(recursiveCost(a, b, 0, 0), expected)

if __name__ == "__main__":
    unittest.main()