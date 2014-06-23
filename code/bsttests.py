import unittest
from lib.bst import (
    BinarySearchTree
)

class TestBinarySearchTree(unittest.TestCase):

    def testInit(self):
        expected = 10
        tree = BinarySearchTree(expected)
        self.assertEqual(tree.left, None)
        self.assertEqual(tree.right, None)
        self.assertEqual(tree.data, expected)

    def testSearchForData(self):

        tree = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        for i in l:
            self.assertTrue(tree.search(i))

        self.assertFalse(tree.search(-1))

    def testInOrder(self):
        tree = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        gen = tree.inOrder()
        l.sort()  # inOrder gives the elements in sorted Order always in BinaryTree
        for i in l:
            self.assertEqual(i, gen.next())

    def testPreOrder(self):
        tree = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        for v in tree.preOrder():
            #print v
            pass
            #ToDo: Test the post Order Sequence

    def testPostOrder(self):
        tree = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        #ToDo: Test the post Order Sequence

    def testDelete(self):
        tree = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        # delete elements one by one and verify that it doesn't exist
        deleted = []
        for x in l:
            deleted.append(x)
            tree = tree.delete(x)

            #verfiy all other elements exist
            checks = [d for d in l if d not in deleted]
            for v in checks:
                self.assertTrue(tree and tree.search(v))

            #verify x doesn't exist
            self.assertFalse(tree and tree.search(x))

    def testMax(self):
        tree = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)
        expected = max(l)
        self.assertEqual(expected, tree.max())

    def testMin(self):
        tree = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)
        expected = min(l)
        self.assertEqual(expected, tree.min())

    def testCountNoOfNodes(self):
        tree = BinarySearchTree()
        l = range(100)
        for d in l:
            tree.insert(d)
        self.assertEqual(tree.size(), len(l))

    def testDepth(self):
        tree = BinarySearchTree()
        l = range(100)
        for d in l:
            tree.insert(d)
        self.assertEqual(tree.getDepth(), len(l))

        tree1 = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree1.insert(d)

        self.assertEqual(tree1.getDepth(), 4)

    def testHasPathSum(self):
        tree = BinarySearchTree()
        l = range(100)
        s = 0
        for d in l:
            tree.insert(d)
            s += d

        self.assertTrue(tree.hasPathSum(s))

        tree1 = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree1.insert(d)

        expected_sums = [8, 12, 14, 15, 17, 18, 23, 25, 20, 30, 34, 39, 41, 47, 49]
        for e in expected_sums:
            self.assertTrue(tree1.hasPathSum(e))

    def testMirror(self):
        tree = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        tree.mirror()
        # when you do a mirror of a BST, the inOrder gives you elements in descending order
        l.sort(reverse=True)
        inOrderGen = tree.inOrder()

        for v in l:
            self.assertEqual(v, inOrderGen.next())

    def testSameTree(self):
        treeOne = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            treeOne.insert(d)

        treeTwo = BinarySearchTree()
        for d in l:
            treeTwo.insert(d)

        self.assertTrue(treeOne.sameTree(treeTwo))
        self.assertTrue(treeTwo.sameTree(treeOne))


        treeTwo.insert(100)
        self.assertFalse(treeTwo.sameTree(treeOne))

        treeOne.insert(100)
        self.assertTrue(treeTwo.sameTree(treeOne))

if __name__ == "__main__":
    unittest.main()