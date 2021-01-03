#construct the call graph from the csv file
from collections import defaultdict
class CallGraph(object):
    def __init__(self):
        self.__graph = defaultdict()

    def add_edge(self, u, v):
        self.__graph.setdefault(u,[]).append(v)

    def compute_backward_traversal(self):
        