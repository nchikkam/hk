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

    def testIsConnected(self):
        self.assertTrue(self.g.isConnected())


        self.g.addVertex(10)
        self.assertFalse(self.g.isConnected())

        """
            g = { "a" : ["d"],
          "b" : ["c"],
          "c" : ["b", "c", "d", "e"],
          "d" : ["a", "c"],
          "e" : ["c"],
          "f" : []
        }
        """
        g = Graph()
        vertices = ['a', 'b', 'c', 'd', 'e', 'f']
        for v in vertices:
            g.addVertex(v)

        g.addEdge('a', 'd')
        g.addEdge('b', 'c')
        g.addEdge('c', 'd')
        g.addEdge('c', 'e')

        self.assertFalse(g.isConnected('a'))

        """
            g2 = {
           "a" : ["d","f"],
           "b" : ["c"],
           "c" : ["b", "c", "d", "e"],
           "d" : ["a", "c"],
           "e" : ["c"],
           "f" : ["a"]
        }
        """

        g2 = Graph()
        vertices = ['a', 'b', 'c', 'd', 'e', 'f']
        for v in vertices:
            g2.addVertex(v)

        g2.addEdge('a', 'd')
        g2.addEdge('a', 'f')
        g2.addEdge('b', 'c')
        g2.addEdge('c', 'b')
        g2.addEdge('c', 'd')
        g2.addEdge('d', 'a')
        g2.addEdge('d', 'c')
        g2.addEdge('c', 'e')
        g2.addEdge('e', 'c')
        g2.addEdge('f', 'a')

        self.assertTrue(g2.isConnected('a'))

        """
            g3 = {
           "a" : ["d","f"],
           "b" : ["c","b"],
           "c" : ["b", "c", "d", "e"],
           "d" : ["a", "c"],
           "e" : ["c"],
           "f" : ["a"]
        }
        """
        g3 = Graph()
        vertices = ['a', 'b', 'c', 'd', 'e', 'f']
        for v in vertices:
            g3.addVertex(v)

        g3.addEdge('a', 'd')
        g3.addEdge('a', 'f')
        g3.addEdge('b', 'c')
        g3.addEdge('b', 'b')
        g3.addEdge('c', 'b')
        g3.addEdge('c', 'c')
        g3.addEdge('c', 'd')
        g3.addEdge('c', 'e')
        g3.addEdge('d', 'a')
        g3.addEdge('d', 'c')
        g3.addEdge('e', 'c')
        g3.addEdge('f', 'a')

        self.assertTrue(g3.isConnected('a'))

    def testCLRDfs(self):

        paths = self.g.CLR_Dfs()
        self.assertEqual(len(paths), 1)

        self.g.addEdge(1, 0, 2) # add a edge from 1 to 0 to make possible paths 2
        paths = self.g.CLR_Dfs()
        self.assertEqual(len(paths), 2)

    def test_BFS(self):

        ss_g = Graph()
        for v in range(6):
            ss_g.addVertex(v)

        ss_g.addEdge(0, 1)
        ss_g.addEdge(0, 4)
        ss_g.addEdge(0, 5)
        ss_g.addEdge(1, 2)
        ss_g.addEdge(2, 3)
        ss_g.addEdge(3, 4)

        (discovered, parents) = ss_g.BFS(0)
        expectePath = [0, 1, 2, 3]
        vPath = []
        ss_g.findPath(0, 3, parents, vPath)
        for (x, y) in zip(expectePath, vPath):
            self.assertEqual(x, y)

        # add an edge between 4 and 3 to short cut for testing new path
        ss_g.addEdge(4, 3)
        (discovered, parents) = ss_g.BFS(0)
        expectePath = [0, 4, 3]
        vPath = []
        ss_g.findPath(0, 3, parents, vPath)
        for (x, y) in zip(expectePath, vPath):
            self.assertEqual(x, y)

    def testFindPath(self):

        g = Graph()

        g.addVertex('s')
        g.addVertex('u')
        g.addVertex('v')
        g.addVertex('t')

        g.addEdge('s', 'u', 20)
        g.addEdge('s', 'v', 10)
        g.addEdge('u', 'v', 30)
        g.addEdge('u', 't', 10)
        g.addEdge('v', 't', 20)

        p = g.find_path('s', 't', [])
        self.assertTrue(all(x in p for x in ['s', 'u', 't']))

    def testFindAllPaths(self):

        g = Graph()

        g.addVertex('s')
        g.addVertex('u')
        g.addVertex('v')
        g.addVertex('t')

        g.addEdge('s', 'u', 20)
        g.addEdge('s', 'v', 10)
        g.addEdge('u', 'v', 30)
        g.addEdge('u', 't', 10)
        g.addEdge('v', 't', 20)

        paths = g.find_all_paths('s', 't', [])
        expectedPaths = [
                         ['s', 'u', 't'],
                         ['s', 'u', 'v', 't'],
                         ['s', 'v', 't']
                         ]
        for path in expectedPaths:
            self.assertTrue(path in paths)

    def testFindShortestPath(self):

        g = Graph()

        g.addVertex('s')
        g.addVertex('u')
        g.addVertex('v')
        g.addVertex('t')

        g.addEdge('s', 'u', 20)
        g.addEdge('s', 'v', 10)
        g.addEdge('u', 'v', 30)
        g.addEdge('u', 't', 10)
        g.addEdge('v', 't', 20)

        expectedPath = ['s', 'u', 't']
        actualPath = g.find_shortest_path('s', 't', [])

        for v in expectedPath:
            self.assertTrue(v in actualPath)

    def testPrims(self):
        expectedMST = [(0, 2, 4), (2, 4, 1), (4, 3, 1), (4, 6, 2), (2, 1, 3), (4, 5, 5)]
        actualMST = self.g.mspPrims()

        for edge in expectedMST:
            self.assertTrue(edge in actualMST)

        # second example
        grph = Graph()
        for v in range(8):
            grph.addVertex(v)

        grph.addEdge(0, 1, 4)
        grph.addEdge(0, 2, 6)
        grph.addEdge(0, 3, 16)
        grph.addEdge(1, 5, 24)
        grph.addEdge(2, 5, 23)
        grph.addEdge(2, 4, 5)
        grph.addEdge(2, 3, 8)
        grph.addEdge(3, 4, 10)
        grph.addEdge(3, 7, 21)
        grph.addEdge(4, 5, 18)
        grph.addEdge(4, 6, 11)
        grph.addEdge(4, 7, 14)
        grph.addEdge(5, 6, 9)
        grph.addEdge(6, 7, 7)

        expMST = [(0, 1, 4), (0, 2, 6), (2, 4, 5), (2, 3, 8), (4, 6, 11), (6, 7, 7), (6, 5, 9)]
        actualMST = grph.mspPrims()

        for edge in expMST:
            self.assertTrue(edge in actualMST)

        # third example
        grph = Graph()
        for v in range(7):
            grph.addVertex(v)

        grph.addEdge(0, 1, 4)
        grph.addEdge(0, 2, 8)
        grph.addEdge(1, 2, 9)
        grph.addEdge(1, 3, 8)
        grph.addEdge(1, 4, 10)
        grph.addEdge(2, 3, 2)
        grph.addEdge(2, 5, 1)
        grph.addEdge(3, 4, 7)
        grph.addEdge(3, 5, 9)
        grph.addEdge(4, 5, 5)
        grph.addEdge(4, 6, 6)
        grph.addEdge(5, 6, 2)

        expMST = [(0, 1, 4), (0, 2, 8), (2, 5, 1), (2, 3, 2), (5, 6, 2), (5, 4, 5)]
        actualMST = grph.mspPrims()
        for edge in expMST:
            self.assertTrue(edge in actualMST)

        # fourth example
        grph = Graph()
        for v in range(6):
            grph.addVertex(v)

        grph.addEdge(0, 1, 2)
        grph.addEdge(0, 2, 3)
        grph.addEdge(1, 2, 6)
        grph.addEdge(1, 3, 5)
        grph.addEdge(1, 4, 3)
        grph.addEdge(2, 4, 2)
        grph.addEdge(3, 4, 1)
        grph.addEdge(3, 5, 2)
        grph.addEdge(4, 5, 4)

        expMST = [(0, 1, 2), (0, 2, 3), (2, 4, 2), (4, 3, 1), (3, 5, 2)]
        actualMST = grph.mspPrims()
        for edge in expMST:
            self.assertTrue(edge in actualMST)

    def testKrushkals(self):

        expectedMST = [(2, 4, 1), (3, 4, 1), (4, 6, 2), (1, 2, 3), (0, 2, 4), (4, 5, 5)]
        actualTree = self.g.mspKrushkals()
        for edge in expectedMST:
            self.assertTrue(edge in actualTree)

        # second example
        grph = Graph()
        for v in range(7):
            grph.addVertex(v)

        grph.addEdge(0, 1, 5)
        grph.addEdge(0, 2, 7)
        grph.addEdge(1, 2, 9)
        grph.addEdge(1, 3, 6)
        grph.addEdge(1, 5, 15)
        grph.addEdge(2, 4, 8)
        grph.addEdge(2, 5, 7)
        grph.addEdge(3, 5, 8)
        grph.addEdge(3, 6, 11)
        grph.addEdge(4, 5, 5)
        grph.addEdge(5, 6, 9)

        expTree = [(0, 1, 5), (4, 5, 5), (1, 3, 6), (0, 2, 7), (2, 5, 7), (5, 6, 9)]
        actualTree = grph.mspKrushkals()
        for edge in expTree:
            self.assertTrue(edge in actualTree)

    def testFloyds(self):

        expected = {
            0: {0: 0,   1: 6,   2: 4,   3: 13,  4: 5,   5: 10,   6: 7 },
            1: {0: float('inf'), 1: 0,   2: 3,
                3: 12,  4: 4,   5: 7,   6: 6
                },
            2: {0: float('inf'), 1: float('inf'),
                2: 0,   3: 9,   4: 1,   5: 6,   6: 3
                },
            3: {0: float('inf'), 1: float('inf'), 2: float('inf'),
                3: 0,   4: 1,   5: 6,   6: 3
                },
            4: {0: float('inf'), 1: float('inf'), 2: float('inf'),
                3: float('inf'), 4: 0,   5: 5,   6: 2
                },
            5: {0: float('inf'), 1: float('inf'), 2: float('inf'),
                3: float('inf'), 4: float('inf'), 5: 0,   6: float('inf')
                },
            6: {0: float('inf'), 1: float('inf'), 2: float('inf'),
                3: float('inf'), 4: float('inf'), 5: float('inf'), 6: 0
                }
        }

        actual = self.g.floyds()
        self.assertDictEqual(expected, actual)  # handy
        self.assertTrue(p==q for p, q in  zip(expected.items(), actual.items())) #does the same
        self.assertTrue(expected.items() == actual.items())  #does the same

        """
            grph = {0: {0: 0,   1: 1,   2: 4},
             1: {0: inf, 1: 0,   2: 2},
             2: {0: inf, 1: inf, 2: 0}
            }
        """
        grph = Graph()
        for v in range(3):
            grph.addVertex(v)

        grph.addEdge(0, 1, 1)
        grph.addEdge(0, 2, 4)
        grph.addEdge(1, 2, 2)

        """
        {0: {0: 0,   1: 1,   2: 3},
         1: {0: inf, 1: 0,   2: 2},
         2: {0: inf, 1: inf, 2: 0}}
        """
        expected = {0: {0: 0,   1: 1,   2: 3},
                    1: {0: float('inf'), 1: 0,   2: 2},
                    2: {0: float('inf'), 1: float('inf'), 2: 0}
                }
        actual = grph.floyds()

        self.assertDictEqual(expected, actual)  # handy
        self.assertTrue(p==q for p, q in  zip(expected.items(), actual.items())) #does the same
        self.assertTrue(expected.items() == actual.items())  #does the same

    def testReachability(self):   #uses floyd's algorithm

        expected = {
            0: {0: True,  1: True,  2: True,  3: True,  4: True,  5: True,  6: True},
            1: {0: False, 1: True,  2: True,  3: True,  4: True,  5: True,  6: True},
            2: {0: False, 1: False, 2: True,  3: True,  4: True,  5: True,  6: True},
            3: {0: False, 1: False, 2: False, 3: True,  4: True,  5: True,  6: True},
            4: {0: False, 1: False, 2: False, 3: False, 4: True,  5: True,  6: True},
            5: {0: False, 1: False, 2: False, 3: False, 4: False, 5: True,  6: False},
            6: {0: False, 1: False, 2: False, 3: False, 4: False, 5: False, 6: True}
        }
        actual = self.g.reachability()

        self.assertDictEqual(expected, actual)

    def testPathRecoveryFloydWarshall(self):   #ToDo:
        expectedParentMap = {
            0: {0: -1, 1:  0, 2:  0, 3:  2, 4:  2, 5:  4, 6:  4},
            1: {0: -1, 1: -1, 2:  1, 3:  2, 4:  2, 5:  1, 6:  4},
            2: {0: -1, 1: -1, 2: -1, 3:  2, 4:  2, 5:  4, 6:  4},
            3: {0: -1, 1: -1, 2: -1, 3: -1, 4:  3, 5:  4, 6:  4},
            4: {0: -1, 1: -1, 2: -1, 3: -1, 4: -1, 5:  4, 6:  4},
            5: {0: -1, 1: -1, 2: -1, 3: -1, 4: -1, 5: -1, 6: -1},
            6: {0: -1, 1: -1, 2: -1, 3: -1, 4: -1, 5: -1, 6: -1}
        }

        actualMap = self.g.pathRecoveryFloydWarshall()

        self.assertDictEqual(expectedParentMap, actualMap)

        path = []
        self.g.getFloydPath(actualMap, 0, 6, path)
        self.assertEqual([6, 4, 2, 0], path)

        path = []
        self.g.getFloydPath(actualMap, 0, 5, path)  #always shortest path
        self.assertEqual([5, 4, 2, 0], path)

        path = []
        self.g.getFloydPath(actualMap, 0, 4, path)  #always shortest path
        self.assertEqual([4, 2, 0], path)

        path = []
        self.g.getFloydPath(actualMap, 0, 3, path)  #always shortest path
        self.assertEqual([3, 2, 0], path)

        path = []
        self.g.getFloydPath(actualMap, 0, 2, path)  #always shortest path
        self.assertEqual([2, 0], path)

        path = []
        self.g.getFloydPath(actualMap, 0, 1, path)  #always shortest path
        self.assertEqual([1, 0], path)

        path = []
        self.g.getFloydPath(actualMap, 1, 5, path)  #always shortest path
        self.assertEqual([5, 1], path)

        path = []
        self.g.getFloydPath(actualMap, 1, 6, path)  #always shortest path
        self.assertEqual([6, 4, 2, 1], path)

        path = []
        self.g.getFloydPath(actualMap, 2, 6, path)  #always shortest path
        self.assertEqual([6, 4, 2], path)

        path = []
        self.g.getFloydPath(actualMap, 2, 5, path)  #always shortest path
        self.assertEqual([5, 4, 2], path)


    def testDijkstra(self):
        g = Graph()
        g.addVertex('s')
        g.addVertex('u')
        g.addVertex('v')
        g.addVertex('x')
        g.addVertex('y')

        g.addEdge('s', 'u', 10)
        g.addEdge('s', 'x', 5)

        g.addEdge('u', 'v', 1)
        g.addEdge('u', 'x', 2)

        g.addEdge('v', 'y', 4)

        g.addEdge('x', 'u', 3)
        g.addEdge('x', 'v', 9)
        g.addEdge('x', 'y', 2)

        g.addEdge('y', 's', 7)
        g.addEdge('y', 'v', 6)

        expected =  ['y', 's']
        actual = g.shortestPathDijkstra('y', 's')
        self.assertEqual(expected, actual)

        expected =  ['s', 'x', 'u', 'v']
        actual = g.shortestPathDijkstra('s', 'v')
        self.assertEqual(expected, actual)

        g.updateEdge('s', 'u', 1)
        expected =  ['s', 'u', 'v']
        actual = g.shortestPathDijkstra('s', 'v')
        self.assertEqual(expected, actual)

    def testTarjansSCC(self):
        expected = [('G',), ('B',), ('E', 'F', 'D'), ('C',), ('A',)]
        g = Graph()
        g.addVertex('A')
        g.addVertex('B')
        g.addVertex('C')
        g.addVertex('D')
        g.addVertex('E')
        g.addVertex('F')
        g.addVertex('G')

        g.addEdge('A', 'C', 1)
        g.addEdge('A', 'E', 1)
        g.addEdge('A', 'F', 1)
        g.addEdge('B', 'G', 1)
        g.addEdge('C', 'B', 1)
        g.addEdge('C', 'D', 1)
        g.addEdge('F', 'E', 1)
        g.addEdge('D', 'F', 1)
        g.addEdge('E', 'D', 1)
        g.addEdge('E', 'G', 1)

        self.assertEqual(expected, g.strongly_connected_components())

        #case -2
        expected = [(12, 11, 9, 10, 7, 8), (6, 3), (5, 4, 2), (1,)]
        g2 = Graph()
        for v in range(1, 13):
            g2.addVertex(v)

        g2.addEdge(1, 2, 1)
        g2.addEdge(2, 3, 1)
        g2.addEdge(2, 4, 1)
        g2.addEdge(2, 5, 1)
        g2.addEdge(3, 6, 1)
        g2.addEdge(4, 5, 1)
        g2.addEdge(4, 7, 1)
        g2.addEdge(5, 2, 1)
        g2.addEdge(5, 6, 1)
        g2.addEdge(5, 7, 1)
        g2.addEdge(6, 3, 1)
        g2.addEdge(6, 8, 1)
        g2.addEdge(7, 8, 1)
        g2.addEdge(7, 10, 1)
        g2.addEdge(8, 7, 1)
        g2.addEdge(9, 7, 1)
        g2.addEdge(10, 9, 1)
        g2.addEdge(10, 11, 1)
        g2.addEdge(11, 12, 1)
        g2.addEdge(12, 10, 1)

        self.assertEqual(expected, g2.strongly_connected_components())


    """
        @ToDo: Test Cayley's Theorem. There are n^(n-2) spanning trees of K.n.
    """

if __name__ == "__main__":
    unittest.main()
