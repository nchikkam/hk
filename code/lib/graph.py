import itertools

class Vertex:
    def __init__(self, id):
        self.id = id
        self.neighbours = {}

    def addNeighbour(self, id, weight):
        self.neighbours[id] = weight

    def __str__(self):
        return str(self.id) + ' Neighbours: ' + str(self.neighbours.keys())

    def getNeighbours(self):
        return self.neighbours #.keys()

    def getName(self):
        return self.id

    def getWeight(self, id):
        return self.neighbours[id]

class Graph:

    def __init__(self):
        self.v = {}
        self.count = 0

    def addVertex(self, key):
        self.count += 1
        newV = Vertex(key)
        self.v[key] = newV

    def getVertex(self, id):
        if id in self.v.keys():
            return self.v[id]
        return None

    def __contains__(self, id):
        return id in self.v.keys()

    def addEdge(self, vertexOne, vertexTwo, weight): # vertexOne, vertexTwo, cost-of-the-edge
        if vertexOne not in self.v.keys():
            self.addVertex(vertexOne)
        if vertexTwo not in self.v.keys():
            self.addVertex(vertexTwo)

        self.v[vertexOne].addNeighbour(vertexTwo, weight)

    def getVertices(self):
        return self.v.keys()

    def __iter__(self):
        return iter(self.v.values())

    def getNeighbours(self,  vertex):
        if vertex not in self.v.keys():
            raise "Node %s not in graph" % vertex
        return self.v[vertex].neighbours #.keys()

    def getEdges(self):
        edges = []

        for node in self.v.keys():
            neighbours = self.v[node].getNeighbours()
            for w in neighbours:
                edges.append((node, w, neighbours[w])) #tuple, srcVertex, dstVertex, weightBetween
        return edges

    def findIsolated(self):
        isolated = []
        for node in self.v:
            deadNode = False
            reachable = True
            # dead node, can't reach any other node from this
            if len(self.v[node].getNeighbours()) == 0:
                deadNode = True

            # reachable from other nodes ?
            nbrs = [n.neighbours.keys() for n in self.v.values()]
            # flatten the nested list
            nbrs = list(itertools.chain(*nbrs))

            if node not in nbrs:
                reachable = False

            if deadNode == True and reachable == False:
                isolated.append(node)

        return isolated

    def getPath(self, start, end, path=[]):
        path = path + [start]
        if start == end:
            return path
        if start not in self.v:
            return None
        for vertex in self.v[start].getNeighbours():
            if vertex not in path:
                extended_path = self.getPath(vertex,
                                            end,
                                            path)
                if extended_path:
                    return extended_path
        return None

    def getAllPaths(self, start, end, path=[]):
        path = path + [start]
        if start == end:
            return [path]
        if start not in self.v:
            return []

        paths = []
        for vertex in self.v[start].getNeighbours():
            if vertex not in path:
                extended_paths = self.getAllPaths(vertex,
                                                  end,
                                                  path)
                for p in extended_paths:
                    paths.append(p)
        return paths

    def inDegree(self, vertex):
        """
           how many edges coming into this vertex
        """
        nbrs = [n.neighbours.keys() for n in self.v.values()]
        # flatten the nested list
        nbrs = list(itertools.chain(*nbrs))

        return nbrs.count(vertex)

    def outDegree(self, vertex):
        """
           how many vertices are neighbours to this vertex
        """
        adj_vertices =  self.v[vertex].getNeighbours()
        return len(adj_vertices)


    """
       The degree of a vertex is the no of edges connecting to it.
       loop is counted twice
       for an undirected Graph deg(v) = indegree(v) + outdegree(v)
    """
    def getDegree(self, vertex):
        return self.inDegree(vertex) + self.outDegree(vertex)

    def verifyDegreeSumFormula(self):
        """Handshaking lemma - Vdeg(v) = 2 |E| """
        degSum = 0
        for v in self.v:
            degSum += self.getDegree(v)

        return degSum == (2* len(self.getEdges()))

