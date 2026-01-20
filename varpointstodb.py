import sqlite3
from sqlite3 import Error
from typing import Set, List, Tuple, Dict, Optional
import time
from collections import namedtuple, defaultdict

from utils import DATABASE_PATH
from bitsets import bitset


class VarPointsToTable:
    var_types: Set[str]

    def __init__(self, benchmark: str, analysis: str, ir: str) -> None:
        self.db = f'{benchmark}_{analysis}_{ir}'

    def __len__(self) -> int:
        """Return the number of records in the database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        try:
            query = f'SELECT count(*) from {self.db}'
            results = conn.execute(query)
            for res in results:
                return res[0]
        except Error as e:
            print(e)
        return 0

    def __repr__(self) -> str:
        return f'VarPointsToTable [table name = {self.db}]'

    def __str__(self) -> str:
        return self.__repr__()

    def get_heap_types(self) -> List[str]:
        """Get all distinct heap types."""
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            query = f'SELECT DISTINCT heapType from {self.db}'
            results = conn.execute(query)
            return [r[0] for r in results]
        except Error as e:
            print(f"get_heap_types: {e}")
            return []

    def get_var_enclosing_method(self) -> Set[str]:
        """Get all distinct enclosing methods."""
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            query = f'SELECT DISTINCT enclosingMethod from {self.db}'
            results = conn.execute(query)
            return {r[0] for r in results}
        except Error as e:
            print(f"get_var_types: {e}")
            return set()

    def all_variables_ctx_pair(self) -> Set[Tuple[str, str]]:
        """Return a set of all variables and context pairs."""
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            query = f'SELECT varCtx, var from {self.db}'
            results = conn.execute(query)
            return {(r[0], r[1]) for r in results}
        except Error as e:
            print(f"all_variables_ctx_pair: {e}")
            return set()

    def all_heap_ctx_pair(self) -> List[Tuple[str, str]]:
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            query = f"SELECT heapCtx, heapObj from {self.db}"
            results = conn.execute(query)
            return [(r[0], r[1]) for r in results]
        except Error as e:
            print(f"all_heap_ctx_pair: {e}")
            return []

    def variables_of_enclosed_method(self, var_typs: Tuple[str, ...]) -> Set[Tuple[str, str]]:
        """
        Return variables of the given enclosing methods.

        Parameters
        ----------
        var_typs : Tuple[str, ...]
            Tuple of enclosing method types

        Returns
        -------
        Set[Tuple[str, str]]
            Set of (varCtx, var) pairs
        """
        conn = sqlite3.connect(DATABASE_PATH)
        var_ctx_pairs: Set[Tuple[str, str]] = set()
        if len(var_typs) == 1:
            query = f"SELECT varCtx, var from {self.db} where enclosingMethod = '{var_typs[0]}'"
        else:
            query = f"SELECT varCtx, var from {self.db} where enclosingMethod in {var_typs}"

        try:
            res = conn.execute(query)
            for r in res:
                var_ctx_pairs.add((r[0], r[1]))
            return var_ctx_pairs
        except Error as e:
            print(f"variables_of_type: {e}")
            print(var_typs)
            print(query)
            return var_ctx_pairs

    def variables_by_enclosed_method_class(self, klasses: Tuple[str, ...]) -> Set[Tuple[str, str]]:
        """Return variables by their enclosed method class."""
        conn = sqlite3.connect(DATABASE_PATH)
        var_ctx_pairs: Set[Tuple[str, str]] = set()
        if len(klasses) == 1:
            query = f"SELECT varCtx, var from {self.db} where varType = '{klasses[0]}'"
        else:
            query = f"SELECT varCtx, var from {self.db} where varType in {klasses}"
        try:
            res = conn.execute(query)
            for r in res:
                var_ctx_pairs.add((r[0], r[1]))
            return var_ctx_pairs
        except Error as e:
            print(f"variables_by_enclosed_method_class: {e}")
            print(query)
            return var_ctx_pairs

    def count_nb_of_variables_method(self) -> Dict[str, int]:
        """
        Return count of distinct variables per enclosing method.

        Returns
        -------
        Dict[str, int]
            Mapping of method to variable count
        """
        conn = sqlite3.connect(DATABASE_PATH)
        query = f"SELECT enclosingMethod, count(distinct var) from {self.db} group by enclosingMethod"
        try:
            res = conn.execute(query)
            return dict(res)
        except Error as e:
            print(f"count_nb_of_variables_by_type: {e}")
            return {}

    def number_vars_type(self, typ: str) -> int:
        return len(self.variables_of_enclosed_method((typ,)))

    def distinct_heap_objs_for_variables(self, var_ctxs: Set[Tuple[str, str]]) -> List[Tuple[str, str]]:
        return list(set(self.heap_objs_for_var(var_ctxs)))

    def heap_objs_for_var(self, var_ctxs: Optional[Set[Tuple[str, str]]]) -> List[Tuple[str, str]]:
        """
        Get heap objects for given variable contexts.

        Parameters
        ----------
        var_ctxs : Optional[Set[Tuple[str, str]]]
            Set of (varCtx, var) pairs

        Returns
        -------
        List[Tuple[str, str]]
            List of (heapCtx, heapObj) pairs
        """
        start_time = time.time()
        if var_ctxs is not None:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            var_ctx_list = [v[0] for v in var_ctxs]
            vars_list = [v[1] for v in var_ctxs]
            cases_query_varctx = ", ".join([f"'{x}'" for x in var_ctx_list])
            cases_query_vars = ", ".join([f"'{x}'" for x in vars_list])
            cases_query_varctx = f'({cases_query_varctx})'
            cases_query_vars = f'({cases_query_vars})'
            try:
                query = (
                    f"SELECT heapCtx, heapObj "
                    f"from {self.db} "
                    f"where varCtx in {cases_query_varctx} and var in {cases_query_vars} "
                    f"and heapObj not like '%null%'"
                )
                res = cursor.execute(query).fetchall()
                print(f"\t\t\tFetched {len(res)} rows in {time.time() - start_time} seconds")
                return [(r[0], r[1]) for r in res]
            except Error as e:
                print(f"heap_objs_for_var: {e}, {query}")
                return []
        return []

    def pointsto_map(self) -> Dict:
        """
        Create points-to map from variables to heap objects.

        Returns
        -------
        Dict
            Mapping of variables to bitset of heap objects
        """
        heap_ctx_pairs = set(self.all_heap_ctx_pair())
        HeapObjs = bitset('HeapObjs', tuple(heap_ctx_pairs))
        pointsto_map = defaultdict(lambda: HeapObjs.infimum)

        HeapVarRow = namedtuple('HeapVarRow', ['var', 'heap'])
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            start = time.time()
            query = f'select varCtx, var, heapCtx, heapObj from {self.db} order by var asc, varCtx asc'
            print("\t\tCreating points-to map")
            count = 0
            for row in cursor.execute(query):
                hvrow = HeapVarRow((row[0], row[1]), (row[2], row[3]))
                var = hvrow.var
                heap_objs = hvrow.heap
                pointsto_map[var] = pointsto_map[var].union(HeapObjs([heap_objs]))
                count += 1
            print(f"\t\tCreated {count} points-to map entries in {time.time() - start} seconds")
            return pointsto_map
        except Error as e:
            print(f"VarPointsToTable:select_all_heap_variables: {e}")
            print(query)
            return pointsto_map

    def number_of_heap_objs(self, var_ctx: Tuple[str, str]) -> int:
        return len(self.heap_objs_for_var({var_ctx}))

    def get_database_size(self) -> int:
        return len(self.db)

    def get_variables_for_heap_obj(self, heap_obj: Tuple[str, str]) -> List[Tuple[str, str]]:
        """Get variables pointing to a given heap object."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            start = time.time()
            query = f'select varCtx, var from {self.db} where heapCtx = {heap_obj[0]} and heapObj = {heap_obj[1]}'
            print(query)
            reverse_points_to = []
            for row in cursor.execute(query):
                reverse_points_to.append((row[0], row[1]))
            return reverse_points_to
        except Error as e:
            print(f"VarPointsToTable:get_variables_for_heap_obj: {e}")
            print(query)
            return []