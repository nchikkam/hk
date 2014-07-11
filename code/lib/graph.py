class Vertex:
    def __init__(self, id):
        self.id = id
        self.neighbours = {}

    def addNeighbour(self, id, weight):
        self.neighbours[id] = weight

    def __str__(self):
        return str(self.id) + ' Neighbours: ' + str(self.neighbours.keys())

    def getNeighbours(self):
        return self.neighbours.keys()

    def getName(self):
        return self.id

    def getWeight(self, id):
        return self.neighbours[id]

class Graph:

    def __init__(self):
        self.v = {}
        self.degree = 0

    def addVertex(self, key):
        self.degree += 1
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



