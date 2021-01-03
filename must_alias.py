import time
from varpointstodb import VarPointsToTable
from collections import defaultdict
from disjoint_set import DisjointSet


class MustAlias(object):
    def __init__(self, benchmark, analysis, ir):
        self._bm = benchmark
        self._analysis = analysis
        self._ir = ir
        self.table = VarPointsToTable(benchmark, analysis, ir)

    def __repr__(self):
        return f"MustAlias (benchmark= {self._bm}, analysis= {self._analysis}, ir= {self._ir}"

    def __str__(self):
        return self.__repr__()

    def compute_must_alias(self):
        pointsto_map = self.table.pointsto_map()
        variables = pointsto_map.keys()
        alias_sets = DisjointSet()
        print(f"\t\t#Variables= {len(variables)}")

        """A O(N logN) algorithm to unify variables. Brute-force approach matches (u,v)  and unifies them if pt(u) = pt(v). 
        This approach maintains a list of visited_heap_objects which maps the integer representation of set of heap 
        objects. If a matching heap objects is found in the visited_heap_objects then the variables are unified,  
        otherwise it updates the visited_heap_objects."""
        visited_heap_objects = defaultdict()
        for v_i in variables:
            heap_objs = int(pointsto_map[v_i])
            if heap_objs in visited_heap_objects.keys():
                v_j = visited_heap_objects[heap_objs]
                if not alias_sets.connected(v_i, v_j):
                    alias_sets.union(v_i, v_j)
            else:
                alias_sets.find(v_i)
            visited_heap_objects[heap_objs] = v_i
        return alias_sets.itersets()
