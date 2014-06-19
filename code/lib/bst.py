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