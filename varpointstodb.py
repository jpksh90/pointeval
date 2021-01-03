import sqlite3
from sqlite3 import Error
from typing import Set, List, Tuple
import time

from utils import DATABASE_PATH
from collections import namedtuple, defaultdict
from bitsets import bitset


class VarPointsToTable:
    var_types: Set[str]

    def __init__(self, benchmark, analysis, ir):
        self.db = f'{benchmark}_{analysis}_{ir}'

    def __len__(self):
        """returns the number of records in the database"""
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        try:
            query = f'SELECT count(*) from {self.db}'
            results = conn.execute(query)
            # get the number of rows in the database
            for res in results:
                return res[0]
        except Error as e:
            print(e)

    def __repr__(self):
        return 'VarPointsToTable [table name = {}]'.format(self.db)

    def __str__(self):
        return self.__repr__()

    def get_heap_types(self):
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            query = f'SELECT DISTINCT heapType from {self.db}'
            results = conn.execute(query)
            return [r[0] for r in results]
        except Error as e:
            print("get_heap_types", e)

    def get_var_enclosing_method(self):
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            query = f'SELECT DISTINCT enclosingMethod from {self.db}'
            results = conn.execute(query)
            res = {r[0] for r in results}
            return res
        except Error as e:
            print("get_var_types", e)

    def all_variables_ctx_pair(self):
        """Return a list of all variables and context pairs
        :return:
        """
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            query = f'SELECT varCtx, var from {self.db}'
            results = conn.execute(query)
            return {(r[0], r[1]) for r in results}
        except Error as e:
            print("all_variables_ctx_pair", e)

    def all_heap_ctx_pair(self):
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            query = f"SELECT heapCtx, heapObj from {self.db}"
            # f" where heapObj not like '%null%'"
            results = conn.execute(query)
            return [(r[0], r[1]) for r in results]
        except Error as e:
            print("all_heap_ctx_pair", e)

    def variables_of_enclosed_method(self, var_typs):
        """
        returns the variable of the types in the tuple var_typ
        :param var_typ: list of types
        :return:
        """
        conn = sqlite3.connect(DATABASE_PATH)
        var_ctx_pairs = set()
        # hack to bypass the stupid tuple printing
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
            print("variables_of_type", e)
            print(var_typs)
            print(query)

    def variables_by_enclosed_method_class(self, klasses):
        conn = sqlite3.connect(DATABASE_PATH)
        var_ctx_pairs = set()
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
            print("variables_by_enclosed_method_class", e)
            print(query)

    def count_nb_of_variables_method(self):
        """
        returns a pair (variable types, x) where x is the number of variables for a particular type
        :param var_type:
        :return:
        """
        conn = sqlite3.connect(DATABASE_PATH)
        query = f"SELECT enclosingMethod, count(distinct var) from {self.db} group by enclosingMethod"
        try:
            res = conn.execute(query)
            return dict(res)
        except Error as e:
            print("count_nb_of_variables_by_type", e)

    def number_vars_type(self, typ):
        return len(self.variables_of_enclosed_method(typ))

    def distinct_heap_objs_for_variables(self, var_ctxs):
        return list(set(self.heap_objs_for_var(var_ctxs)))

    def heap_objs_for_var(self, var_ctxs):
        """
        Takes a list of vars and contexts and computes the points-to set for each (var,ctx)
        :param var_ctxs: List<(<Variable,Ctx>) or a single <Variable,Ctx>
        :return:
        """
        start_time = time.time()
        if var_ctxs is not None:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            # not a clean way to do this. But still works....
            varCtxs = list(v[0] for v in var_ctxs)
            vars = list(v[1] for v in var_ctxs)
            cases_query_varctx = ", ".join(list(map(lambda x: f"'{x}'", varCtxs)))
            cases_query_vars = ", ".join(list(map(lambda x: f"'{x}'", vars)))
            cases_query_varctx = f'({cases_query_varctx})'
            cases_query_vars = f'({cases_query_vars})'
            try:
                query = f"SELECT heapCtx, heapObj " \
                        f"from {self.db} " \
                        f"where varCtx in {cases_query_varctx} and var in {cases_query_vars} " \
                        f"and heapObj not like '%null%'"
                res = cursor.execute(query).fetchall()
                print(f"\t\t\tFetched {len(res)} rows in {time.time() - start_time} seconds")
                return [(r[0], r[1]) for r in res]
            except Error as e:
                print("heap_objs_for_var", e, query)

    def pointsto_map(self):
        """pointsto_map maps variables to set of heap-objects. Set of heap-objects are backed by a bitset mapping
                for space efficiency"""
        # initialize the HeapObjs to a bitvector and pointsto_map
        heap_ctx_pairs = set(self.all_heap_ctx_pair())
        HeapObjs = bitset('HeapObjs', tuple(heap_ctx_pairs))
        pointsto_map = defaultdict(lambda: HeapObjs.infimum)

        HeapVarRow = namedtuple('HeapVarRow', ['var', 'heap'])
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            start = time.time()
            query = f'select varCtx, var, heapCtx, heapObj from {self.db} order by var asc, varCtx asc'
            # res = set(map(HeapVarRow._make, cursor.execute(query).fetchall()))
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
            print("VarPointsToTable:select_all_heap_variables", e)
            print(query)

    def number_of_heap_objs(self, var_ctx):
        return len(self.heap_objs_for_var(var_ctx))

    def get_database_size(self):
        return len(self.db)

    def get_variables_for_heap_obj(self, heap_obj):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            start = time.time()
            query = f'select varCtx, var from {self.db} where heapCtx = {heap_obj[0]} and heapObj = {heap_obj[1]}'
            print(query)
            reverse_points_to = []
            for row in cursor.execute(query):
                reverse_points_to.append((row[0],row[1]))
            return reverse_points_to
        except Error as e:
            print("VarPointsToTable:get_variables_for_heap_obj")
            print(query)