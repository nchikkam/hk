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
