import os
import sqlite3
from sqlite3 import Error
from utils import get_heap_type_info

DATABASE_PATH = os.path.join(".", "db", "varpointsto.db")
ANALYSIS_LOG_ROOT = "analysis-logs"
LOG_FILE_NAME = 'Stats_Simple_Application_VarPointsTo.csv'


def load_var_points_to_db(benchmark, analysis, ir):
    dir_name = f'{benchmark}_{ir}'
    log_file = os.path.join(".", ANALYSIS_LOG_ROOT, analysis, dir_name, "database", LOG_FILE_NAME)
    print("log file name", log_file)
    db_entries = []
    # with open(log_file, 'r') as fh:
    try:
        fh = open(log_file, 'r')
        for line in fh:
            pts_info = line.split('\t')  # tuple of form (heapCtx, heapObj, varCtx, var)
            heap_type = get_heap_type_info(pts_info[1])
            var_enclosing_method = get_var_method_info(pts_info[3])
            pts_info.append(heap_type)
            pts_info.append(var_enclosing_method)
            pts_info.append(get_var_type_info(pts_info[3]))
            db_entries.append(tuple(pts_info))
    except FileNotFoundError as e:
        print(f"Error = {e}")


    table_name = '{}_{}_{}'.format(benchmark, analysis, ir)
    # create table if not exists
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    try:
        query = f'CREATE TABLE IF NOT EXISTS {table_name} (heapCtx string,' \
                f' heapObj string,' \
                f' varCtx string,' \
                f' var string,' \
                f' heapType string,' \
                f' enclosingMethod string,' \
                f' varType string)'
        print(query)
        cur.execute(query)
        conn.commit()
    except Error as e:
        print(e)
    # populate tables
    try:
        query = f"INSERT INTO {table_name} VALUES (?,?,?,?,?,?,?)"
        print(query)
        cur.executemany(query, db_entries)
        conn.commit()
        print(f'Populated database entries {cur.rowcount}')
    except Error as e:
        print(e)


def get_var_method_info(variable):
    """Extracts the type information of the containing method and class name in a variable."""
    pos_angle = variable.find('<')
    pos_colon = variable.find('>')
    if pos_colon != -1 and pos_angle != -1:
        return variable[pos_angle + 1:pos_colon]
    else:
        return variable


def get_var_type_info(variable: str):
    """Extracts the type information of the containign method"""
    pos_angle = variable.find('<')
    pos_colon = variable.find(':')
    if pos_colon != -1 and pos_angle != -1:
        return variable[pos_angle + 1:pos_colon]
    else:
        return variable


if __name__ == '__main__':
    benchmarks = ['avrora', 'batik', 'eclipse', 'h2', 'jython', 'lusearch', 'luindex', 'pmd', 'sunflow', 'tradebeans', 'xalan']
    benchmarks.remove('eclipse')
    benchmarks.remove('jython')
    analyses = ['2os']

    # benchmarks = ['eclipse', 'jython']

    print(f'Analysis = {analyses}')
    print(f'Benchmarks = {benchmarks}')
    input('Press enter to continue.... ')
    irs = ['wala', 'soot']
    for ir in irs:
        for b in benchmarks:
            for a in analyses:
                print(f"Loading table analysis={a} benchmark={b}  ir={ir}.......")
                load_var_points_to_db(analysis=a, benchmark=b, ir=ir)
                print("COMPLETED")
