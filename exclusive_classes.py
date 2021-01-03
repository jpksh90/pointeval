import sqlite3
from sqlite3 import Error


def _exclusive_classes(benchmark: str, from_ir: str, to_ir: str):
    conn = sqlite3.connect('pointeval.db')
    cur = conn.cursor()
    query_template = f"select class_name from class_info where benchmark='{benchmark}' and framework='{from_ir}' except" \
                     f" select class_name from class_info where benchmark='{benchmark}' and framework='{to_ir}'"
    try:
        res = cur.execute(query_template)
        # print(f'Exclusive Classes: Fetched {cur.rowcount} rows')
        return {r[0] for r in res}
    except Error as e:
        print(e)


def exclusive_classes_soot(benchmark):
    return _exclusive_classes(benchmark, "jimple", "wala")


def exclusive_classes_wala(benchmark):
    return _exclusive_classes(benchmark, "wala", "jimple")
