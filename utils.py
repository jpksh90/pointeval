from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from tabulate import tabulate
from scipy.stats import wilcoxon

DATABASE_PATH = Path(".") / "db" / "varpointsto.db"


def get_type_info(variable: str) -> str:
    """Extracts the type information in a variable."""
    pos_angle = variable.find('<')
    pos_colon = variable.find(':')
    if pos_colon != -1 and pos_angle != -1:
        return variable[pos_angle + 1:pos_colon]
    return variable


def print_wilcoxon_results(
    results: List[Dict[str, Any]],
    fields: tuple,
    msg: str,
    file_handler: TextIO,
) -> None:
    x_col = [i[fields[0]] for i in results]
    y_col = [i[fields[1]] for i in results]
    w, p = wilcoxon(x=x_col, y=y_col, zero_method='zsplit', mode="approx")
    file_handler.write(f"\n{msg} : w = {w}, p = {p}")


def pretty_print_latex(precision_matrix: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, 'w') as fh:
        pretty_print_stats(precision_matrix, fh, mode="latex")


def pretty_print_stats(
    precision_matrix: List[Dict[str, Any]],
    fh: TextIO,
    mode: str = "simple",
) -> None:
    headers = list(precision_matrix[0].keys())
    table_values = [list(x.values()) for x in precision_matrix]
    if mode == "latex":
        fh.write(tabulate(table_values, headers=tuple(headers), tablefmt="latex_booktabs"))
    elif mode == "simple":
        fh.write(tabulate(table_values, headers=tuple(headers), tablefmt="simple"))
    else:
        raise ValueError("Mode can be either simple or latex")


def pretty_print_csv(precision_matrix: List[Dict[str, Any]], file_name: str) -> None:
    headers = list(precision_matrix[0].keys())
    values = [list(x.values()) for x in precision_matrix]
    with open(file_name, 'w+') as fh:
        fh.write(','.join(headers))
        fh.write('\n')
        for value in values:
            str_values = [str(x) for x in value]
            fh.write(','.join(str_values))
            fh.write('\n')


def pp_dictionary(dictionary: Dict[str, Any]) -> None:
    """
    Pretty print a dictionary where the keys are string. Handle special cases for numeric values.
    """
    for k, v in dictionary.items():
        if isinstance(v, int):
            print(f'{k:25s}', f'{v:,}')
        elif isinstance(v, float):
            print(f'{k:25s}', f'{v:.2f}')
        else:
            print(f'{k:25s}', v)


def get_heap_type_info(heap_object: str) -> str:
    if heap_object.startswith("<<"):
        return heap_object
    if heap_object.startswith("<") and heap_object.endswith(">"):
        pos_1 = heap_object.find('<')
        pos_2 = heap_object.find('>')
        return heap_object[pos_1 + 1:pos_2]
    if "(Tamiflex)" in heap_object:
        pos_1 = heap_object.rfind('/')
        pos_2 = heap_object.rfind('>')
        return heap_object[pos_1 + 1: pos_2]
    pos_1 = heap_object.find('/') + 4
    pos_2 = heap_object.rfind('/')
    return heap_object[pos_1 + 1: pos_2]
