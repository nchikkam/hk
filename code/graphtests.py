import unittest
from lib.graph import (
    Graph
)

class GraphTests(unittest.TestCase):

    def testBasic(self):

        g = Graph()
        for v in range(6):
            g.addVertex(v)

        g.addEdge(0,1,5)
        g.addEdge(0,5,2)
        g.addEdge(1,2,4)
        g.addEdge(2,3,9)
        g.addEdge(3,4,7)
        g.addEdge(3,5,3)
        g.addEdge(4,0,1)
        g.addEdge(5,4,8)
        g.addEdge(5,2,1)

        for v in g:
            for w in v.getNeighbours():
                print("( %s , %s )" % (v.getName(), w))

        self.assertTrue(True)



if __name__ == "__main__":
    unittest.main()