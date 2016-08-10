import unittest
from lib.bst import (
    BinarySearchTree,
    BinaryTree
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

    def testDiameter(self):
        bstOne = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bstOne.insert(d)

        self.assertEqual(bstOne.diameter(), 7)

        # single node
        b = BinarySearchTree()
        b.insert(8)
        self.assertEqual(b.diameter(), 1)

        b.insert(4)
        self.assertEqual(b.diameter(), 2)


        bstTwo = BinarySearchTree()
        l = [8, 2, 1, 4, 5, 3, 9, 10, 15, 13, 12, 14, 18]
        for v in l:
            bstTwo.insert(v)

        self.assertEqual(bstTwo.diameter(), 9)

    def testRadius(self):
        """
        Given a binary tree find all the nodes at k distance from a given node.
       """
        bst = BinarySearchTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            bst.insert(d)

        k2list = [2, 6, 10, 14]
        k3list = [1, 3, 5, 7, 9, 11, 13, 15]
        k2gen = bst.getRadiusList(2)
        for v in k2gen:
            self.assertTrue(v in k2list)

        k3gen = bst.getRadiusList(3)
        for v in k3gen:
            self.assertTrue(v in k3list)

        k1gen = bst.getRadiusList(1)
        for v in k1gen:
            self.assertTrue(v in [4, 12])

        k0gen = bst.getRadiusList(0)
        for v in k0gen:
            self.assertTrue(v in [8])


        # try with different tree structure
        """
                       8             -----------------> radius 0 =>[8]
                    /    \
                 2         9         -----------------> radius 1 =>[2, 9]
               /  \         \
             1     4         10      -----------------> radius 2 =>[1, 4, 10]
                  / \          \
                3    5         15    -----------------> radius 3 =>[3, 5, 15]
                              /  \
                            13    18 -----------------> radius 1 =>[13, 18]
                           /  \
                         12    14    -----------------> radius 1 =>[12, 14]
        """
        bstTwo = BinarySearchTree()
        l = [8, 2, 1, 4, 5, 3, 9, 10, 15, 13, 12, 14, 18]
        for v in l:
            bstTwo.insert(v)

        k3gen = bstTwo.getRadiusList(3)
        k3list = [3, 5, 15]
        for v in k3gen:
            self.assertTrue(v in k3list)

        k4gen = bstTwo.getRadiusList(4)
        k4list = [13, 18]
        for v in k4gen:
            self.assertTrue(v in k4list)

        k5gen = bstTwo.getRadiusList(5)
        k5list = [12, 14]
        for v in k5gen:
            self.assertTrue(v in k5list)

#class TestBinaryTree(unittest.TestCase):
    """
    Given a binary tree serialize the tree such that it can be retrieved in the same form again
    Merge two binary search trees [http://disqus.com/alienonearth/]
    Find the maximum path sum between two leaves of a binary tree
    Nice Link: https://www.cs.duke.edu/~ola/courses/cps100spr96/tree/trees.html
    checck the 12 points problem on the above page
    """
    def testBinaryTreeCreate(self):
        l = [-15, 5, 6, -8, 1, 3, 9, 2, 6, None, None, None, None, 4, 0, None, None, None, None, None, None, None, -1, 10, None]
        """
                  -15
                 /    \
                5      6
              /  \    / \
            -8    1  3   9
           /  \        /  \
         2     6      4    6
                            \
                            -1
                           /
                         10

        """
        bt = BinaryTree()
        bt.create(l)

        expectedInorder = [2, -8, 6, 5, 1, -15, 3, 6, 4, 9, 0, 10, -1]
        g = bt.inOrder()
        for v in expectedInorder:
            self.assertEqual(v, g.next())

    def testBTGetMaxPathSum(self):
        l = [-15, 5, 6, -8, 1, 3, 9, 2, 6, None, None, None, None, 4, 0, None, None, None, None, None, None, None, -1, 10, None]
        bt = BinaryTree()
        bt.create(l)

        self.assertEqual(bt.getMaxPathSum()[1], 27)

    def testSum(self):
        l = [-15, 5, 6, -8, 1, 3, 9, 2, 6, None, None, None, None, 4, 0, None, None, None, None, None, None, None, -1, 10, None]
        s = 0
        for v in l:
            if v: s += v

        bt = BinaryTree()
        bt.create(l)

        self.assertEqual(bt.sum(), s)

        bstTwo = BinarySearchTree()
        l = [8, 2, 1, 4, 5, 3, 9, 10, 15, 13, 12, 14, 18]
        for v in l:
            bstTwo.insert(v)

        self.assertEqual(bstTwo.sum(), sum(l))

    def testBSTSymmetricity(self):

        # Single node
        l = [9]
        bt = BinaryTree()
        bt.create(l)

        # case-1:
        l = [8, 4, 4, 1, 3, 3, 1]
        """
                  8     -> This Binary Tree is Symmetric
                /  \
               4    4
             /  \  / \
           1    3 3   1
        """
        bt = BinaryTree()
        bt.create(l)

        self.assertTrue(bt.isSymmetric(True))



        self.assertTrue(bt.isSymmetric(True))

        l = [8, 4, 4, None, 3, 3, None]
        """
                  8
                /  \
               4    4
                \  /
                3 3
        """
        bt = BinaryTree()
        bt.create(l)

        self.assertTrue(bt.isSymmetric(True))

        l = [8, 4, 4, None, 3, 3, 1, None, None, None, None, None, None]
        """
                  8
                /  \
               4    4
                \  / \
                3 3   1
        """
        bt = BinaryTree()
        bt.create(l)

        self.assertFalse(bt.isSymmetric())

        # case-2:
        l = [8, 4, 4, 1, None, None, 1, None, None, None, None]
        """
                  8
                /  \
               4    4
             /       \
            1         1
        """
        bt = BinaryTree()
        bt.create(l)

        self.assertTrue(bt.isSymmetric(True))

        # case-2.1:
        l = [8, 4, 4, 1, 3, None, 1, None, None, None, None, None, None]
        """
                  8
                /  \
               4    4
             /  \    \
            1   3     1
        """
        bt = BinaryTree()
        bt.create(l)

        self.assertFalse(bt.isSymmetric(True))

        # case-3
        l = [8, 4, 4, 2, 2, 2, 2, -2, 9, 9, -2, -2, 9, 9, -2, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]
        """
                     8     -> This Binary Tree is Symmetric
                 /      \
               4          4
             /  \        /  \
           2     2      2    2
         /  \   / \    / \   / \
       -2   9  9  -2  -2  9 9  -2
        """
        bt = BinaryTree()
        bt.create(l)

        self.assertTrue(bt.isSymmetric(True))

        # compare just the structure and exclude data from the comparison
        l = [8, 4, 5, 4, 9, 8, 7]
        """
                  8     -> This Binary Tree is Symmetric
                /  \
               4    5
             /  \  / \
           4    9 8   7
        """
        bt = BinaryTree()
        bt.create(l)

        self.assertTrue(bt.isSymmetric(False)) # don't compare data, but structure ;)

    def testLeftOnlyDepthOfANode(self):
        l = [8, 4, 4, 1, 3, None, 1, None, None, None, None, None, None]
        """
                  8
                /  \
               4    4
             /  \    \
            1   3     1
        """
        bt = BinaryTree()
        bt.create(l)
        self.assertEqual(bt.getLeftDepth(), 2)
        self.assertEqual(bt.left.getLeftDepth(), 1)
        self.assertEqual(bt.right.getLeftDepth(), 0)

    def testRightOnlyDepthOfANode(self):
        l = [8, 4, 4, 1, 3, None, 1, None, None, None, None, None, None]
        """
                  8
                /  \
               4    4
             /  \    \
            1   3     1
        """
        bt = BinaryTree()
        bt.create(l)
        self.assertEqual(bt.getRightDepth(), 2)
        self.assertEqual(bt.left.getRightDepth(), 1)

    """
    A binary tree is either an empty tree or a node (called the root) consisting
    of a single integer value and two further binary trees, called the left subtree
    and the right subtree.

    For example, the figure below shows a binary tree consisting of six nodes.
    Its root contains the value 5, and the roots of its left and right subtrees
    have the values 3 and 10, respectively. The right subtree of the node containing
    the value 10, as well as the left and right subtrees of the nodes containing
    the values 20, 21 and 1, are empty trees.

                   5
                /    \
               3      10
             /  \     /
            20   21  1

    A path in a binary tree is a non-empty sequence of nodes that one can traverse
    by following the pointers. The length of a path is the number of pointers it
    traverses. More formally, a path of length K is a sequence of nodes
    P[0], P[1], ..., P[K], such that node P[I + 1] is the root of the left or right
    subtree of P[I], for 0 ≤ I < K. For example, the sequence of nodes with values
    5, 3, 21 is a path of length 2 in the tree from the above figure. The sequence
    of nodes with values 10, 1 is a path of length 1. The sequence of nodes with
    values 21, 3, 20 is not a valid path.

    The height of a binary tree is defined as the length of the longest possible
    path in the tree. In particular, a tree consisting of only one node has height 0
    and, conventionally, an empty tree has height −1. For example, the tree shown in
    the above figure is of height 2.

    Problem
    Write a function that, given a non-empty binary tree T consisting of N nodes,
    returns its height. For example, given tree T shown in the figure above, the function
    should return 2, as explained above. Note that the values contained in the nodes
    are not relevant in this task.
    """
    def testMaxLengthPathEitherLeftOnlyOrRightOnlyConcentratedSearch(self):
        def solution(T):
            def get_left_depth(N):  # O(log N)
                """just finds out the left height"""
                if N:
                    if N.left:
                        l = get_left_depth(N.left)
                        return l + 1
                    return 0
                return 0

            def get_right_depth(N):  # O(log N)
                """just finds out the right height"""
                if N:
                    if N.right:
                        r = get_right_depth(N.right)
                        return r + 1
                    return 0
                return 0

            lengths = {}  # container to store the path lengths

            # standard bfs algorithm O(N)
            def bfsTraversal(N):
                q = []  # queue to store the nodes in BFS Order
                index = 0
                if N.left == None and N.right == None:
                    return
                q.append(N)
                while len(q) > 0:
                    current = q.pop(0)
                    lengths[index] = max(get_left_depth(current.left), get_right_depth(current.right)) + 1
                    index += 1
                    if current.left:
                        q.append(current.left)
                    if current.right:
                        q.append(current.right)

            bfsTraversal(T)
            sol = -1
            for k in lengths:  # O(N)
                if sol < int(lengths[k]):
                    sol = int(lengths[k])

            return sol

        # it doesn't matter if the tree is BT or BST
        """
                   5
                /    \
               3      10
             /  \     /
            20   21  1
        """
        l = [5, 3, 10, 20, 21, 1, None]
        bt = BinaryTree()
        bt.create(l)
        self.assertEqual(2, solution(bt))



if __name__ == "__main__":
    unittest.main()