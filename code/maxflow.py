import unittest
from lib.flownetwork import (
    FlowNetwork
)

class MaxFlowNetowrkTests(unittest.TestCase):

    def testBasic(self):
        ntwrk = FlowNetwork()
        for v in "sopqrt":
            ntwrk.add_vertex(v)

        ntwrk.add_edge('s','o',3)
        ntwrk.add_edge('s','p',3)
        ntwrk.add_edge('o','p',2)
        ntwrk.add_edge('o','q',3)
        ntwrk.add_edge('p','r',2)
        ntwrk.add_edge('r','t',3)
        ntwrk.add_edge('q','r',4)
        ntwrk.add_edge('q','t',2)
        self.assertEqual(ntwrk.max_flow('s','t'), 5)

if __name__ == "__main__":
    unittest.main()



