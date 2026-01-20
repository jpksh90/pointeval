import sqlite3
from sqlite3 import Error
from typing import Set


def _exclusive_classes(benchmark: str, from_ir: str, to_ir: str) -> Set[str]:
    """Get exclusive classes found in one IR but not the other."""
    conn = sqlite3.connect('pointeval.db')
    cur = conn.cursor()
    query_template = (
        f"select class_name from class_info where benchmark='{benchmark}' and framework='{from_ir}' except "
        f"select class_name from class_info where benchmark='{benchmark}' and framework='{to_ir}'"
    )
    try:
        res = cur.execute(query_template)
        return {r[0] for r in res}
    except Error as e:
        print(e)
        return set()


def exclusive_classes_soot(benchmark: str) -> Set[str]:
    """Get classes exclusive to Soot (in Soot but not in Wala)."""
    return _exclusive_classes(benchmark, "jimple", "wala")


def exclusive_classes_wala(benchmark: str) -> Set[str]:
    """Get classes exclusive to Wala (in Wala but not in Soot)."""
    return _exclusive_classes(benchmark, "wala", "jimple")
