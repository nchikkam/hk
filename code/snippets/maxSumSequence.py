import unittest
# Function to return max sum such that no two elements
# are adjacent

def findMaxSum(l):
    dp0, dp1 = l[0], 0

    for v in l[1:]:
      temp = max(dp0, dp1) # max up to now

      dp0 = dp1 + v  # max with present value
      dp1 = temp     # max with out present value

    return max(dp0, dp1)
class MaxSumTest(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(80, findMaxSum([5,  5, 10, 40, 50, 35]))
        self.assertEqual(110, findMaxSum([5, 5, 10, 100, 10, 5]))
        self.assertEqual(13, findMaxSum([3,2,7,10]))
        self.assertEqual(13, findMaxSum([3, 2, -5, 10, 7]))


if __name__ == "__main__":
    unittest.main()