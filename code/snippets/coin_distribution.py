"""
Dynamic Programming
Many programs in computer science are written to optimize some value;
for example, find the shortest path between two points, find the line
that best fits a set of points, or find the smallest set of objects
that satisfies some criteria. There are many strategies that computer
scientists use to solve these problems. One of the goals of this book
is to expose you to several different problem solving strategies.
Dynamic programming is one strategy for these types of optimization
problems.

A classic example of an optimization problem involves making change
using the fewest coins. Suppose you are a programmer for a vending
machine manufacturer. Your company wants to streamline effort by giving
out the fewest possible coins in change for each transaction. Suppose a
customer puts in a dollar bill and purchases an item for 37 cents. What
is the smallest number of coins you can use to make change? The answer
is six coins: two quarters, one dime, and three pennies. How did we arrive
at the answer of six coins? We start with the largest coin in our arsenal
(a quarter) and use as many of those as possible, then we go to the next
lowest coin value and use as many of those as possible. This first approach
is called a greedy method because we try to solve as big a piece of the
problem as possible right away.

The greedy method works fine when we are using U.S. coins, but suppose that
your company decides to deploy its vending machines in Lower Elbonia where,
in addition to the usual 1, 5, 10, and 25 cent coins they also have a 21 cent
coin. In this instance our greedy method fails to find the optimal solution
for 63 cents in change. With the addition of the 21 cent coin the greedy
method would still find the solution to be six coins. However, the optimal
answer is three 21 cent pieces.

Lets look at a method where we could be sure that we would find the optimal
answer to the problem. Since this section is about recursion, you may have
guessed that we will use a recursive solution. Lets start with identifying
the base case. If we are trying to make change for the same amount as the
value of one of our coins, the answer is easy, one coin.

If the amount does not match we have several options. What we want is the
minimum of a penny plus the number of coins needed to make change for the
original amount minus a penny, or a nickel plus the number of coins needed
to make change for the original amount minus five cents, or a dime plus the
number of coins needed to make change for the original amount minus ten cents,
and so on. So the number of coins needed to make change for the original
amount can be computed according to the following:

numCoins=min{1+numCoins(originalamount-1)1+numCoins(originalamount-5)1+numCoins(originalamount-10)1+numCoins(originalamount-25)}
The algorithm for doing what we have just described is shown in Listing 7.
In line 3 we are checking our base case; that is, we are trying to make change
in the exact amount of one of our coins. If we do not have a coin equal to
the amount of change, we make recursive calls for each different coin value
less than the amount of change we are trying to make. Line 6 shows how we
filter the list of coins to those less than the current value of change
using a list comprehension. The recursive call also reduces the total amount
of change we need to make by the value of the coin selected. The recursive call
is made in line 7. Notice that on that same line we add 1 to our number of
coins to account for the fact that we are using a coin. Just adding 1 is the
same as if we had made a recursive call asking where we satisfy the base case
condition immediately.
"""
def recMC(coinValueList, change):
    print change
    minCoins = change
    if change in coinValueList:
        return 1
    else:
        for i in [c for c in coinValueList if c <= change]:
            numCoins = 1 + recMC(coinValueList, change-i)
            if numCoins < minCoins:
                minCoins = numCoins
    return minCoins

def recDC(coinValueList, change, knownResults):
    minCoins = change
    if change in coinValueList:
        knownResults[change] = 1
        return 1
    elif knownResults[change] > 0:
        return knownResults[change]
    else:
        for i in [c for c in coinValueList if c <= change]:
            numCoins = 1 + recDC(coinValueList, change-i, knownResults)
            if numCoins < minCoins:
                minCoins = numCoins
                knownResults[change] = minCoins
    return minCoins


"""
DP with memoizatoin
"""
def dpMakeChange(coinValueList,change,minCoins,coinsUsed):
   for cents in range(change+1):
      coinCount = cents
      newCoin = 1
      for j in [c for c in coinValueList if c <= cents]:
            if minCoins[cents-j] + 1 < coinCount:
               coinCount = minCoins[cents-j]+1
               newCoin = j
      minCoins[cents] = coinCount
      coinsUsed[cents] = newCoin
   return minCoins[change]
"""
    def printCoins(coinsUsed,change):
       coin = change
       while coin > 0:
          thisCoin = coinsUsed[coin]
          print(thisCoin)
          coin = coin - thisCoin

    def main():
        amnt = 63
        clist = [1,5,10,21,25]
        coinsUsed = [0]*(amnt+1)
        coinCount = [0]*(amnt+1)

        print("Making change for",amnt,"requires")
        print(dpMakeChange(clist,amnt,coinCount,coinsUsed),"coins")
        print("They are:")
        printCoins(coinsUsed,amnt)
        print("The used list is as follows:")
        print(coinsUsed)
"""

def printCoins(coinsUsed,change):
       coin = change
       while coin > 0:
          thisCoin = coinsUsed[coin]
          print(thisCoin)
          coin = coin - thisCoin


import unittest
class CoinDistributionTest(unittest.TestCase):
    #def test_check_for_6_coins_reCMC(self):
    #    self.assertEqual(6, recMC([1,5,10,25], 63))
        #self.assertEqual(3, recMC([1,5], 7))

    def test_check_for_6_coins_recDC(self):
        self.assertEqual(6, recDC([1,5,10,25], 63, [0]*64))

    def test_check_for_3_coins_recDC(self):
        self.assertEqual(3, recDC([1,5,10,21,25], 63, [0]*64))

    def test_check_for_6_coins_DPBackTrackMatrix(self):
        amnt = 63
        clist = [1,5,10,21,25]
        coinsUsed = [0]*(amnt+1)
        coinCount = [0]*(amnt+1)
        self.assertEqual(6, dpMakeChange([1,5,10,25], 63, coinsUsed, coinCount))

if __name__ == "__main__":
    unittest.main()