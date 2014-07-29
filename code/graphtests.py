import unittest
from lib.graph import (
    Graph
)

class GraphTests(unittest.TestCase):

    def setUp(self):

        self.g = Graph()
        for v in range(7):
            self.g.addVertex(v)

        self.g.addEdge(0, 1, 6)
        self.g.addEdge(0, 2, 4)
        self.g.addEdge(1, 2, 3)
        self.g.addEdge(1, 5, 7)
        self.g.addEdge(2, 3, 9)
        self.g.addEdge(2, 4, 1)
        self.g.addEdge(3, 4, 1)
        self.g.addEdge(4, 5, 5)
        self.g.addEdge(4, 6, 2)

    def tearDown(self):
        self.g = None

    def testBasic(self):
        for v in self.g.getVertices():
            self.assertTrue(v in range(7))

    def testNeighbours(self):
        zero_s_nbrs = [1, 2]
        for v in zero_s_nbrs:
            self.assertTrue(v in self.g.getNeighbours(0))

        one_s_nbrs = [2, 5]
        for v in one_s_nbrs:
            self.assertTrue(v in self.g.getNeighbours(1))

        two_s_nbrs = [3, 4]
        for v in two_s_nbrs:
            self.assertTrue(v in self.g.getNeighbours(2))

        three_s_nbrs = [4]
        for v in three_s_nbrs:
            self.assertTrue(v in self.g.getNeighbours(3))

        four_s_nbrs = [5, 6]
        for v in four_s_nbrs:
            self.assertTrue(v in self.g.getNeighbours(4))

    def testEdges(self):
        expected_edges = [
            (0, 1, 6),
            (0, 2, 4),
            (1, 2, 3),
            (1, 5, 7),
            (2, 3, 9),
            (2, 4, 1),
            (3, 4, 1),
            (4, 5, 5),
            (4, 6, 2)
        ]
        edges = self.g.getEdges()
        for edge in expected_edges:
            self.assertTrue(edge in edges)

    def testIsolatedVertex(self):
        self.g.addVertex(10)
        isolated = self.g.findIsolated()
        self.assertTrue(10 in isolated)

    def testGetPath(self):
        path = self.g.getPath(0, 6, [])
        self.assertEquals(path, [0, 1, 2, 3, 4, 6])

        path = self.g.getPath(0, 10, [])
        self.assertEquals(None, path)

    def testGetAllPaths(self):
        expectedPaths = [[0, 1, 2, 3, 4, 6],
                         [0, 1, 2, 4, 6],
                         [0, 2, 3, 4, 6],
                         [0, 2, 4, 6]
                        ]
        paths = self.g.getAllPaths(0, 6, [])

        for path in expectedPaths:
            self.assertTrue(path in paths)


if __name__ == "__main__":
    unittest.main()