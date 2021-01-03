from tabulate import tabulate
from scipy.stats import wilcoxon
import os

DATABASE_PATH = os.path.join(".", "db", "varpointsto.db")


def get_type_info(variable):
    """Extracts the type information in a variable."""
    posAngle = variable.find('<')
    posColon = variable.find(':')
    if (posColon != -1 and posAngle != -1):
        return variable[posAngle + 1:posColon]
    else:
        return variable


def print_wilcoxon_results(results, fields, msg, file_handler):
    x_col = [i[fields[0]] for i in results]
    y_col = [i[fields[1]] for i in results]
    w, p = wilcoxon(x=x_col, y=y_col, zero_method='zsplit', mode="approx")
    file_handler.write(f"\n{msg} : w = {w}, p = {p}")


def pretty_print_latex(precision_matrix, filepath):
    fh = open(filepath, 'w')
    pretty_print_stats(precision_matrix, fh, mode="latex")
    fh.close()


def pretty_print_stats(precision_matrix, fh, mode="simple"):
    headers = list(precision_matrix[0].keys())
    table_values = [list(x.values()) for x in precision_matrix]
    if mode == "latex":
        fh.write(tabulate(table_values, headers=tuple(headers), tablefmt="latex_booktabs"))
    elif mode == "simple":
        fh.write(tabulate(table_values, headers=tuple(headers), tablefmt="simple"))
    else:
        raise ValueError("Mode can be either simple or latex")


def pretty_print_csv(precision_matrix, file_name):
    headers = list(precision_matrix[0].keys())
    values = [list(x.values()) for x in precision_matrix]
    with open(file_name, 'w+') as fh:
        fh.write(','.join(headers))
        fh.write('\n')
        for value in values:
            str_values = [str(x) for x in value]
            fh.write(','.join(str_values))
            fh.write('\n')


def pp_dictionary(dictionary):
    """
    Pretty print a dictionary where the keys are string. Handle special cases for numeric values
    :param dictionary:
    :return:
    """
    for k, v in dictionary.items():
        if type(v) == int:
            print(f'{k:25s}', f'{v:,}')
        elif type(v) == float:
            print(f'{k:25s}', f'{v:.2f}')
        else:
            print(f'{k:25s}', v)


def get_heap_type_info(heap_object: str):
    if heap_object.startswith("<<"):
        return heap_object
    elif heap_object.startswith("<") and heap_object.endswith(">"):
        pos_1 = heap_object.find('<')
        pos_2 = heap_object.find('>')
        return heap_object[pos_1 + 1:pos_2]
    elif ("(Tamiflex)" in heap_object):
        # get the type of Tamiflex object
        pos_1 = heap_object.rfind('/')
        pos_2 = heap_object.rfind('>')
        return heap_object[pos_1 + 1: pos_2]
    else:
        pos1 = heap_object.find('/') + 4  # skip the new declaration
        pos2 = heap_object.rfind('/')
        return heap_object[pos1 + 1: pos2]
