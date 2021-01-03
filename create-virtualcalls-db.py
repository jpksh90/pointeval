import os
import sqlite3
from sqlite3 import Error

DATABASE_PATH = os.path.join(".", "db", "varpointsto.db")
ANALYSIS_LOG_ROOT = "analysis-logs"
LOG_FILE_NAME = 'VirtualMethodInvocation.csv'


def load_var_points_to_db(benchmark, analysis, ir):
    dir_name = f'{benchmark}_{ir}'
    log_file = os.path.join(".", ANALYSIS_LOG_ROOT, analysis, dir_name, "database", LOG_FILE_NAME)
    print("log file name", log_file)
    db_entries = []
    try:
        fh = open(log_file, 'r')
        for line in fh:
            pts_info = tuple(line.split('\t'))  # tuple of form (heapCtx, heapObj, varCtx, var)
            db_entries.append(pts_info)
    except FileNotFoundError as e:
        print(f"Error = {e}")

    table_name = f'virtualcall_var_{benchmark}_{analysis}_{ir}'
    # create table if not exists
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    try:
        query = f'CREATE TABLE IF NOT EXISTS {table_name} (virtualCallSite string,' \
                f' virtualVar string)'
        print(query)
        cur.execute(query)
        conn.commit()
    except Error as e:
        print(e)
    # populate tables
    try:
        query = f"INSERT INTO {table_name} VALUES (?,?)"
        print(query)
        cur.executemany(query, db_entries)
        conn.commit()
        print(f'Populated database entries {cur.rowcount}')
    except Error as e:
        print(e)


if __name__ == '__main__':
    benchmarks = ['avrora', 'batik', 'eclipse', 'h2', 'jython', 'lusearch', 'luindex', 'pmd', 'sunflow', 'tradebeans', 'xalan']
    # benchmarks = ['avrora']
    benchmarks.remove('eclipse')
    benchmarks.remove('jython')
    analyses = ['2os']
    print(f'Analysis = {analyses}')
    print(f'Benchmarks = {benchmarks}')
    input('Press enter to continue.... ')
    irs = ['wala', 'soot']
    for ir in irs:
        for b in benchmarks:
            for a in analyses:
                print(f"Starting analysis={a} benchmark={b}  ir={ir}")
                load_var_points_to_db(analysis=a, benchmark=b, ir=ir)
                print(f"Completed analysis={a} benchmark={b}  ir={ir}")

