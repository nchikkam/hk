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

    def testCountTrees(self):  #Assumes only Binary Tree, doesn't have to be a BST
        self.assertEqual(BinarySearchTree.countTrees(0), 1)
        self.assertEqual(BinarySearchTree.countTrees(1), 1)
        self.assertEqual(BinarySearchTree.countTrees(2), 2)
        self.assertEqual(BinarySearchTree.countTrees(3), 5)
        self.assertEqual(BinarySearchTree.countTrees(4), 14)
        self.assertEqual(BinarySearchTree.countTrees(6), 132)
        self.assertEqual(BinarySearchTree.countTrees(7), 429)
        self.assertEqual(BinarySearchTree.countTrees(10), BinarySearchTree.catalan(10))

    def testIsBST(self):
        bstOne = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bstOne.insert(d)

        self.assertTrue(bstOne.isBST())


        bstTwo = BinarySearchTree()
        l = range(100)
        for d in l:
            bstTwo.insert(d)

        self.assertTrue(bstTwo.isBST())

    def todoTestIsBSTNegativeCase(self):
        leveOrder = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        bt = BinaryTree()
        for d in levelOrder:
            bt.inSertInLevelOrder(d)

        self.assertFalse(bt)

    def testCommonAncestor(self):
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)

        self.assertEqual(bst.commonAncestor(4, 12), 8)
        self.assertEqual(bst.commonAncestor(4, 10), 8)
        self.assertEqual(bst.commonAncestor(4, 14), 8)
        self.assertEqual(bst.commonAncestor(1, 15), 8)

    def testSpaceEfficientTraversal(self):
        bstOne = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bstOne.insert(d)

        bstTwo = bstOne
        clone = bstOne

        genOne = bstTwo.spaceEfficientTraversal()
        genTwo = bstOne.inOrder()
        l.sort()  # inOrder gives the elements in sorted Order always in BinaryTree
        for i in l:
            self.assertEqual(i, genOne.next())
            self.assertEqual(i, genTwo.next())


        #create a copyTree method in the API and use it to test the similarity[Deep Copy]
        self.assertTrue(bstOne.sameTree(clone))

    def printTreeToList(self):
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)

        blist = bst.treeToList()
        bst.printList(blist)

    def testbstClone(self):
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)
        clone = bst.bstClone()
        self.assertTrue(bst.sameTree(clone))

    def testInorderSuccessor(self):
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)

        self.assertEqual(bst.right.inOrderSuccessor().data, bst.right.right.left.data)
        self.assertEqual(bst.left.inOrderSuccessor().data, bst.left.right.left.data)
        self.assertEqual(bst.right.right.inOrderSuccessor().data, bst.right.right.right.data)

    def testGetLeafCount(self):
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)

        self.assertEqual(bst.getLeafCount(), 8)

        bst = BinarySearchTree()
        bst.insert(2)
        bst.insert(1)
        self.assertEqual(bst.getLeafCount(), 1)

        bst.insert(3)
        self.assertEqual(bst.getLeafCount(), 2)

    def testGetInternalNodesCount(self):
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)

        #self.assertEqual(bst.getInternalNodesCount(), 7)

    def testWellOrderedNess(self):
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)

        self.assertTrue(bst.wellOrdered())

        bst.left.data = 300
        self.assertFalse(bst.wellOrdered())

    def testBreadthFirstTraversal(self):
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)

        expectedBFSOrder = [8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15]

        gen = bst.bfsTraversal()
        for expectedValue in expectedBFSOrder:
            self.assertEqual(expectedValue, gen.next())

    def testCreateBSTFromTwoTraversals(self):
        inOrder  = [1, 2, 3, 4, 5, 6 ,7 ,8 ,9, 10, 11, 12, 13, 14, 15]
        preOrder = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        bstFromTraversals = BinarySearchTree.createBSTFromTwoTraversals(inOrder, preOrder, 0, len(inOrder)-1)

        bst = BinarySearchTree()
        l = [8, 12, 4, 14, 2, 6, 10, 9, 7, 5, 11, 13, 3, 1, 15]
        for v in l:
            bst.insert(v)

        self.assertTrue(bst.sameTree(bstFromTraversals))

if __name__ == "__main__":
    unittest.main()