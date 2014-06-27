import unittest
from lib.dp import (
    cost,
    findEditDistance
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
                 ("atcat", "attatc", 2),
                 ("a", "b", 1),
                 ("a", "a", 0),
                 ("a", "ab", 1),
                 ("a", "aa", 1),
                 ("a", "bb", 2),
                ]

        for (a, b, expected) in data:
            self.assertEqual(cost(a, b), expected)
            self.assertEqual(findEditDistance(a, b), expected)

if __name__ == "__main__":
    unittest.main()