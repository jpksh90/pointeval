import sqlite3
from sqlite3 import Error
from utils import DATABASE_PATH

class VirtualCallVariablesTable(object):
    def __init__(self, benchmark: str, analysis: str, ir: str):
        self._benchmark = benchmark
        self._analysis = analysis
        self._ir = ir
        self.table_name = f'virtualcall_var_{benchmark}_{analysis}_{ir}'

    def virtualcall_variables(self):
        """
        returns the set of virtual call variables
        :return:
        """
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        query = f"select DISTINCT virtualVar from {self.table_name}"
        try:
            res = cur.execute(query)
            return {r[0] for r in res}
        except Error as e:
            print(f"{__name__}::virtualcall_variables", e)
