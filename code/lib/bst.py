class BinarySearchTree:

    def __init__(self, data=None):
        self.left = None
        self.right = None
        self.data = data

    def insert(self, data):
        if self.data == None:
            self.data = data
        elif self.data < data:
            if self.right == None:
                self.right = BinarySearchTree(data)
            else:
                self.right.insert(data)
        elif self.data > data:
            if self.left == None:
                self.left = BinarySearchTree(data)
            else:
                self.left.insert(data)
        else:
            print "Trying to Insert Duplicate key"

    def search(self, data):
        if self.data == None:
            return False
        result = False
        if self.data == data:
            return True
        elif self.data < data:
            if self.right is not None:
                result = self.right.search(data)
        else:
            if self.left is not None:
                result = self.left.search(data)
        return result
        """
        Iterative: k
          n = self
          while (n != None) {
            if k < n.data:
                n = n.left
            elif k > n.data:
                n = n.right
            else:
                return True
          return False
        """

    def preOrder(self):
        yield self.data
        if self.left:
            for v in self.left.preOrder():
                yield v
        if self.right:
            for v in self.right.preOrder():
                yield v

    def inOrder(self): #lazy mode, iterators :)
        if self.left:
            for v in self.left.inOrder():
                yield v

        yield self.data

        if self.right:
            for v in self.right.inOrder():
                yield v

    def postOrder(self):
        if self.left:
            for v in self.left.postOrder():
                yield v
        if self.right:
            for v in self.right.postOrder():
                yield v
        yield self.data

    def delete(self, data):
        if data == self.data:
            if self.left:   # internal Node
                self.data = self.left.max()
                self.left = self.left.delete(self.data)
            elif self.right:
                self.data = self.right.min()
                self.right = self.right.delete(self.data)
            else:
                return None
        else:
            if data < self.data and self.left:
                self.left = self.left.delete(data)
            if data > self.data and self.right:
                self.right = self.right.delete(data)
        return self

    def max(self):
        if self.right:
            return self.right.max()
        else:
            return self.data

    def min(self):
        if self.left:
            return self.left.min()
        else:
            return self.data

    def size(self):  #count no of nodes
        n = 0
        if self.left:
            n += self.left.size()
        if self.data != None:
            n += 1
        if self.right:
            n += self.right.size()
        return n

    def findMax(self, a, b):
        return max(a, b)

    def getDepth(self):
        if self.data != None:
            l, r = 0, 0
            if self.left:
                l = self.left.getDepth()
            if self.right:
                r = self.right.getDepth()
            return max(l, r) +1
        return 0

    def hasPathSum(self, sum):
        """
        find if there is a path from root to some node that sums to the given value.
        Strategy: subtract the node value from the sum when recurring down, and check
        to see if the sum is 0 when you run out of tree.
        """
        if self.data != None:
            mSum = sum - self.data
            lHasSum, rHasSum = False, False
            if self.left:
                lHasSum = self.left.hasPathSum(mSum)
            if self.right:
                rHasSum = self.right.hasPathSum(mSum)
            return ( lHasSum or rHasSum or mSum == 0)
        else:
            return ( sum == 0 )

    def mirror(self):
        """
        Change a tree so that the roles of the
        left and right pointers are swapped at every node.

         So the tree...

                       8
                    /    \
                 4         12
               /  \       /  \
             2     6     10   14
           / \    / \   / \   / \
          1   3  5   7 9  11 13  15

         is changed to...
                       8
                    /    \
                 12        4
               /  \       /  \
             14    10    6    2
           / \    / \   / \   / \
          15 13  11  9 7  5  3   1
        """
        if self.data != None:
            if self.left:
                self.left.mirror()
            if self.right:
                self.right.mirror()

            self.left, self.right = self.right, self.left

    def sameTree(self, other):
        """
        return true if self and other are structurally identical
        """
        if (self == None and other == None):
            return True

        if self.data == other.data: #data equal
            lflag = None
            rflag = None
            if self.left == None and other.left==None:
                lflag = True
            elif self.left != None and other.left != None:
                lflag = self.left.sameTree(other.left)
            else:
                lflag = False

            if self.right == None and other.right == None:
                rflag = True
            elif self.right != None and other.right != None:
                rflag = self.right.sameTree(other.right)
            else:
                rflag = False
            return lflag == rflag
        else: # one is empty and the other is not, False
            return False

    @staticmethod
    def countTrees(numKeys):
        if numKeys <= 1: return 1
        # there will be one value at the root, with whatever remains
        # on the left and right each forming their own subtrees.
        # Iterate through all the values that could be the root...
        sum = 0
        for root in range(1, numKeys+1): # 1<=numKeys
            left = BinarySearchTree.countTrees(root-1)
            right = BinarySearchTree.countTrees(numKeys-root)
            # number of possible trees with this root == left*right
            sum += left * right
        return sum

    @staticmethod
    def catalan(n) :
        """
        useful resource(s): http://en.wikipedia.org/wiki/Catalan_number
        """
        if (n == 0): return 1
        res = 0
        for i in range(n):
            res += BinarySearchTree.catalan(i) * BinarySearchTree.catalan(n-i-1);

        return res;

    def isBST(self):
        if self.data == None: return True
        # if min of the left subtree is more than self.data return false
        if self.left:
            if self.left.min() > self.data: return False
        # false if the max of the right is <= than us
        if self.right:
            if self.right.max() <= self.data: return False

        # false if, recursively, the left or right is not a BST
        if self.left:
            if self.left.isBST() == False: return False

        if self.right:
            if self.right.isBST() == False: return False

        #if passed All, its a BST
        return True

    def commonAncestor(self, a, b):
        # negative case, LCA doesn't exist
        if self.data == None or  self.data == a or self.data == b:
            return None

        if a < self.data < b or b < self.data < a:
            return self.data

        # LCA would probably in the Left sub tree
        if self.data > a and self.data > b:
            if self.left:
                return self.left.commonAncestor(a, b)
            else:
                return None
        else:#        if self.data < a and self.data < b:
            if self.right:
                return self.right.commonAncestor(a, b)
            else:
                return None

    def spaceEfficientTraversal(self):
        current = self
        while current != None:
            if current.left == None:
                yield current.data
                current = current.right
            else:
                # find in order predecessor of current make current right of the right most node in the left sub tree
                pre = current.left
                while pre.right != None and pre.right != current:
                    pre = pre.right
                # make current s right child of its in order predecessor
                if pre.right == None:
                    pre.right = current
                    current = current.left
                # revert the pointer back to restore the tree to its original form
                else:
                    pre.right = None
                    yield current.data
                    current = current.right

    # inspiration: http://cslibrary.stanford.edu/109/TreeListRecursion.html
    def bstJoin(self, a, b):
        a.right = b
        b.left = a

    def bstAppend(self, a, b):
        if a == None: return b
        if b == None: return a

        aLast = a.left
        bLast = b.left;

        self.bstJoin(aLast, b);
        self.bstJoin(bLast, a);

        return a

    def treeToList(self):
        if self.data == None:
            return None

        # recursively solve subtrees -- leap of faith!
        alist = None
        if self.left:
            alist = self.left.treeToList()

        blist = None
        if self.right:
            blist = self.right.treeToList()

        # Make a length-1 list ouf of the root
        self.left = self
        self.right = self

        # Append everything together in sorted order
        alist = self.bstAppend(alist, self)
        alist = self.bstAppend(alist, blist)

        return alist

    def printList(self, dblist):
        current = dblist
        print "\n"
        while current != None:
            print current.data,
            current = current.right
            if current == dblist:
                return
        print "\n"

    def bstClone(self):
        if self.data == None:
            return None
        current = BinarySearchTree(self.data)
        if self.left:
            current.left = self.left.bstClone()
        if self.right:
            current.right = self.right.bstClone()

        return current

    def inOrderSuccessor(self):
        if self.right:
            temp = self.right  # same logic as min, but returning the node not value
            while temp.left:
                temp = temp.left
            return temp


        succ = None
        root = self

        while self.data != None:
            if self.data < root.data:
                succ = root
                root = root.left
            elif self.data > root.data:
                root = root.right
            else:
                break
        return succ

    def getLeafCount(self):
        if self.data == None:
            return 0
        if self.left == None and self.right == None:
            return 1
        else:
            c = 0
            if self.left:
                c += self.left.getLeafCount()
            if self.right:
                c += self.right.getLeafCount()
            return c

    def getInternalNodesCount(self):
        if self.left == None and self.right == None:
            return 0
        else:
            c = 0
            if self.left and self.right:
                c += 1

            if self.left:
                c += self.left.getLeafCount()
            if self.right:
                c += self.right.getLeafCount()

            return c

    # compose tree from given two traversal orders
    @staticmethod
    def createBSTFromTwoTraversals(
                                  inOrder,
                                  preOrder,
                                  startIndex,
                                  endIndex):
        if startIndex > endIndex:
            return None

        # make first element in the preOrder list as root
        bst = BinarySearchTree()
        data = preOrder.pop(0)
        bst.insert(data)

        # find the position of this element in the inOrder list
        n = BinarySearchTree.findPosition(inOrder, data, startIndex, endIndex)

        # all the elements left of this 'n' fall in the left sub tree
        bst.left = BinarySearchTree.createBSTFromTwoTraversals(inOrder, preOrder, startIndex, n-1)

        # all the elements right of this 'n' fall in the right sub tree
        bst.right = BinarySearchTree.createBSTFromTwoTraversals(inOrder, preOrder, n+1, endIndex)

        return bst

    @staticmethod
    def findPosition(list, data, st, end):
        while st <= end:
            if list[st] == data:
                return st
            st += 1
        return None

    def wellOrdered(self):
        if self.data == None:
            return True # single node, well ordered.
        elif self.left and self.data < self.left.data:
            return  False
        elif self.right and self.data > self.right.data:
            return False

        leftFlag, rightFlag = True, True
        if self.left:
            leftFlat = self.left.wellOrdered()

        if self.right:
            rightFlag = self.right.wellOrdered()

        return leftFlag and rightFlag

    def bfsTraversal(self):
        q = [] # queue to store the nodes in BFS Order
        if self.data == None:
            return
        q.append(self)
        while len(q) > 0:
            current = q.pop(0)
            yield current.data
            if current.left:
                q.append(current.left)
            if current.right:
                q.append(current.right)


    def diameter(self):
        """
        diametter of a tree is similar to the graph. The max no of nodes or vertices exist
        in the tree with longest path between them.
        """
        if self.data != None:
            lh, rh = 0, 0

            if self.left:
                lh = self.left.getDepth()
            if self.right:
                rh = self.right.getDepth()

            ld, rd = 0, 0
            if self.left:
                ld = self.left.diameter()
            if self.right:
                rd = self.right.diameter()

            return max(lh + rh +1, ld, rd)

        return 0
