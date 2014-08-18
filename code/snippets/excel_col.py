# -*- coding: utf-8 -*-
"""
Excel Column Name Finder
"""
#   Copyright (C) 2014-2058 by
#   Narayana Chikkam<nchikkam@gmail.com>
#   All rights reserved.
__author__ = """Narayana Chikkam (nchikkam@gmail.com)"""
__all__ = ["excel_column_mapper"]

def getNumber(scol):
    base = 1
    digit = 0
    num = 0

    l = len(scol)-1 #index at 0
    while l >=0 :
        digit = (ord(scol[l])-ord('A'))+1
        num = num + (digit * base)
        base *= 26 # raise by 26 ;)
        l = l - 1
    return num-1

def getCol(n):
   str=""
   while n>=0:
       digit = (n%26)
       n = n/26-1
       temp = chr( 65 + digit)
       str = temp + str
   return str;


def getRandomString():
    import random
    len = random.randint(0, 10)
    retStr = ""

    while len > 0:
        ch = random.randint(0, 25)
        retStr = retStr + chr(65 + ch)
        len = len - 1
    return retStr


import unittest
class TestExcelCols(unittest.TestCase):

    def test_IV(self):
        self.assertEqual(255, getNumber("IV"))

    def test_A(self):
        self.assertEqual(0, getNumber("A"))

    def test_XFD(self):
        self.assertEqual(16383, getNumber("XFD"))

    def test_Z(self):
        self.assertEqual(25, getNumber("Z"))

    def test_AA(self):
        self.assertEqual(26, getNumber("AA"))

    def test_255(self):
        self.assertEqual('IV', getCol(255))

    def test_0(self):
        self.assertEqual('A', getCol(0))

    def test_16383(self):
        self.assertEqual('XFD', getCol(16383))

    def test_25(self):
        self.assertEqual('Z', getCol(25))

    def test_26(self):
        self.assertEqual('AA', getCol(26))

    def test_regression(self):
        for v in range(0, 16384):
            actual = getCol(v)
            expected = getNumber(actual)
            #print v, actual, expected
            self.assertEqual(v, expected)

    def test_random_sampler(self):

        for sample_runs in range(0, 100):
            randomString = getRandomString()
            randCol = getNumber(randomString)
            actualString = getCol(randCol)
            #print randomString, actualString, randCol
            self.assertEqual(randomString,  actualString)

if __name__ == "__main__":
    unittest.main()
