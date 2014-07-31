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

    def addEdge(self, vertexOne, vertexTwo, weight=None): # vertexOne, vertexTwo, cost-of-the-edge
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

    def delta(self):
        """ the minimum degree of the Graph V """
        min = 2**64
        for vertex in self.v:
            vertex_degree = self.getDegree(vertex)
            if vertex_degree < min:
                min = vertex_degree
        return min

    def Delta(self):
        """ the maximum degree of the Graph V """
        max = -2**64
        for vertex in self.v:
            vertex_degree = self.getDegree(vertex)
            if vertex_degree > max:
                max = vertex_degree
        return max

    def degreeSequence(self):
        """
           degree sequence is the reverse sorder of the vertices degrees
           Isomorphic graphs have the same degree sequence. However,
           two graphs with the same degree sequence are not necessarily
           isomorphic.
           More-Info:
           http://en.wikipedia.org/wiki/Graph_realization_problem
        """
        seq = []
        for vertex in self.v:
            seq.append(self.getDegree(vertex))
        seq.sort(reverse=True)
        return tuple(seq)

    # helper to check if the given sequence is in non-increasing Order ;)
    @staticmethod
    def sortedInDescendingOrder(seq):
        return all (x>=y for x,y in zip(seq, seq[1:]))

    @staticmethod
    def isGraphicSequence(seq):
      """
       Assumes that the degreeSequence is a list of non negative integers
       http://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Gallai_theorem
      """
      # Check to ensure there are an even number of odd degrees
      if sum(seq)%2 != 0: return False
      # Erdos-Gallai theorem
      for k in range(1, len(seq)+1):
        leftSum = sum(seq[:(k)])
        rightSum = k * (k-1) + sum([min(x, k) for x in seq[k:]])
        if leftSum > rightSum: return False
      return True

    @staticmethod
    def isGraphicSequenceIterative(s):
        # successively reduce degree sequence by removing node of maximum degree
        # as in Havel-Hakimi algorithm
        while s:
            s.sort()    # sort in increasing order
            if s[0]<0:
                return False  # check if removed too many from some node

            d=s.pop()             # pop largest degree
            if d==0: return True  # done! rest must be zero due to ordering

            # degree must be <= number of available nodes
            if d>len(s):   return False

            # remove edges to nodes of next higher degrees
            #s.reverse()  # to make it easy to get at higher degree nodes.
            for i in range(len(s)-1,len(s)-(d+1),-1):
                s[i]-=1

        # should never get here b/c either d==0, d>len(s) or d<0 before s=[]
        return False

    def density(self):
        """
        In mathematics, a dense graph is a graph in which the number of edges
        is close to the maximal number of edges. The opposite, a graph with
        only a few edges, is a sparse graph. The distinction between sparse
        and dense graphs is rather vague, and depends on the context.

        For undirected simple graphs, the graph density is defined as:
        D = (2*No-Of-Edges)/((v*(v-1))/2)
        For a complete Graph, the Density D is 1
        """
        """ method to calculate the density of a graph """
        V = len(self.v.keys())
        E = len(self.getEdges())
        return 2.0 * E / (V *(V - 1))