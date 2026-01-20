import time
from typing import Iterator, Set, Tuple
from collections import defaultdict

from varpointstodb import VarPointsToTable
from disjoint_set import DisjointSet


class MustAlias:
    def __init__(self, benchmark: str, analysis: str, ir: str) -> None:
        self._bm = benchmark
        self._analysis = analysis
        self._ir = ir
        self.table = VarPointsToTable(benchmark, analysis, ir)

    def __repr__(self) -> str:
        return f"MustAlias (benchmark= {self._bm}, analysis= {self._analysis}, ir= {self._ir})"

    def __str__(self) -> str:
        return self.__repr__()

    def compute_must_alias(self) -> Iterator[Set]:
        pointsto_map = self.table.pointsto_map()
        variables = pointsto_map.keys()
        alias_sets = DisjointSet()
        print(f"\t\t#Variables= {len(variables)}")

        visited_heap_objects: dict = defaultdict()
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
