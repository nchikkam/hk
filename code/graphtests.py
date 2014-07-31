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

    def testInDegree(self):
        self.g.addVertex(10)
        expectedDegrees = [(0, 0),  # 0 vertex has 0 edges going to it
                           (1, 1),
                           (2, 2),
                           (3, 1),
                           (4, 2),
                           (5, 2),
                           (6, 1),
                           (10, 0)
                           ]
        for (vertex, inDegree) in expectedDegrees:
            self.assertEqual(self.g.inDegree(vertex), inDegree)

    def testOutDegree(self):
        self.g.addVertex(10)
        expectedDegrees = [(0, 2),  # 0 vertex has 2 edges going from it
                           (1, 2),
                           (2, 2),
                           (3, 1),
                           (4, 2),
                           (5, 0),
                           (6, 0),
                           (10, 0)
                           ]
        for (vertex, outDegree) in expectedDegrees:
            self.assertEqual(self.g.outDegree(vertex), outDegree)

    def testDegree(self):
        self.g.addVertex(10)
        expectedDegrees = [(0, 2),  # 0 vertex has 2 edges
                           (1, 3),
                           (2, 4),
                           (3, 2),
                           (4, 4),
                           (5, 2),
                           (6, 1),
                           (10, 0)
                           ]
        for (vertex, degree) in expectedDegrees:
            self.assertEqual(self.g.getDegree(vertex), degree)

    def testDegreeSumFormula(self):
        self.assertTrue(self.g.verifyDegreeSumFormula())

    def testMinDegreeOfGraphV(self):
        self.assertEqual(self.g.delta(), 1)

        #add a isolated vertex and check the degree 0
        self.g.addVertex(10)
        self.assertEqual(self.g.delta(), 0)

    def testMaxDegreeOfGraphV(self):
        self.assertEqual(self.g.Delta(), 4)

    def testDegreeSequence(self):
        expected = (4, 4, 3, 2, 2, 2, 1)
        self.assertEqual(self.g.degreeSequence(), expected)

    def testErdosGallaiTheorem(self):
        self.assertTrue(Graph.isGraphicSequence([2, 2, 2, 2, 1, 1]))
        self.assertTrue(Graph.isGraphicSequence([3, 3, 3, 3, 3, 3]))
        self.assertTrue(Graph.isGraphicSequence([3, 3, 2, 1, 1]))

        self.assertFalse(Graph.isGraphicSequence([4, 3, 2, 2, 2, 1, 1]))
        self.assertFalse(Graph.isGraphicSequence([6, 6, 5, 4, 4, 2, 1]))
        self.assertFalse(Graph.isGraphicSequence([3, 3, 3, 1]))

    def testHavelHakimiAlgorithm(self):
        self.assertTrue(Graph.isGraphicSequenceIterative([2, 2, 2, 2, 1, 1]))
        self.assertTrue(Graph.isGraphicSequenceIterative([3, 3, 3, 3, 3, 3]))
        self.assertTrue(Graph.isGraphicSequenceIterative([3, 3, 2, 1, 1]))

        self.assertFalse(Graph.isGraphicSequenceIterative([4, 3, 2, 2, 2, 1, 1]))
        self.assertFalse(Graph.isGraphicSequenceIterative([6, 6, 5, 4, 4, 2, 1]))
        self.assertFalse(Graph.isGraphicSequenceIterative([3, 3, 3, 1]))

    def testDensity(self):
        g = Graph()
        vertices = ['a', 'b', 'c', 'd', 'e', 'f']
        for v in vertices:
            g.addVertex(v)

        """
            g = { "a" : ["d","f"],
           "b" : ["c","b"],
           "c" : ["b", "c", "d", "e"],
           "d" : ["a", "c"],
           "e" : ["c"],
           "f" : ["a"]
        }
        """
        g.addEdge('a', 'd')
        g.addEdge('a', 'f')
        g.addEdge('b', 'c')
        g.addEdge('b', 'b')
        g.addEdge('c', 'c')
        g.addEdge('c', 'd')
        g.addEdge('c', 'e')

        self.assertAlmostEqual(0.466666666667, g.density(), places=7)

        """
            complete_graph = {
            "a" : ["b","c"],
            "b" : ["a","c"],
            "c" : ["a","b"]
        }

        """

        complete_graph = Graph()
        vertices = ['a', 'b', 'c']
        for v in vertices:
            complete_graph.addVertex(v)

        complete_graph.addEdge('a', 'b')
        complete_graph.addEdge('a', 'c')
        complete_graph.addEdge('b', 'c')

        self.assertEqual(1.0, complete_graph.density())


        """
        isolated_graph = {
            "a" : [],
            "b" : [],
            "c" : []
        }
        """

        isolated_graph = Graph()
        vertices = ['a', 'b', 'c']
        for v in vertices:
            isolated_graph.addVertex(v)

        self.assertEqual(0.0, isolated_graph.density())


if __name__ == "__main__":
    unittest.main()