# -*- coding: utf-8 -*-
#   Copyright (C) 2014-2058 by
#   Narayana Chikkam<nchikkam@gmail.com>
#   All rights reserved.
__author__ = """Narayana Chikkam (nchikkam@gmail.com)"""
__all__ = ["list_rotator"]

def rotate(l, k):
    left = l[k::-1]            #reverse from index 0 to K
    right = l[len(l):k:-1]     #reverse from index K to end of the string
    ret = left + right
    return ret[::-1] #reverse the whole string

import unittest
class ListRotaterTest(unittest.TestCase):

    def test_4(self):
        l = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        expected = [6, 7, 8, 9, 1, 2, 3, 4, 5]
        self.assertEqual(expected, rotate(l, 4))

    def test_0(self):
        l = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        expected = [2, 3, 4, 5, 6, 7, 8, 9, 1]
        self.assertEqual(expected, rotate(l, 0))

    def test_1(self):
        l = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        expected = [3, 4, 5, 6, 7, 8, 9, 1, 2]
        self.assertEqual(expected, rotate(l, 1))

    def test_6(self):
        l = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        expected = [8, 9, 1, 2, 3, 4, 5, 6, 7]
        self.assertEqual(expected, rotate(l, 6))

    def test_1_1(self):
        l = [1]
        expected = [1]
        self.assertEqual(expected, rotate(l, 0))

if __name__ == "__main__":
    unittest.main()
