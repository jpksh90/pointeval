import argparse
import sys
from pathlib import Path
from typing import List

from computeprecision import ComputePrecision
from utils import pretty_print_csv, pretty_print_latex, pretty_print_stats, print_wilcoxon_results

BENCHMARKS = [
    'avrora', 'batik', 'eclipse', 'h2', 'jython', 'lusearch', 'luindex',
    'pmd', 'sunflow', 'tradebeans', 'xalan'
]


def runner_single_benchmark(analysis: str, benchmark: List[str]) -> None:
    print(f"analysis= {analysis}, benchmark= {benchmark[0]}")
    precision_obj = ComputePrecision(analysis=analysis, benchmark=benchmark[0])
    precision_obj.wala_ir_precision()
    precision_obj.soot_ir_precision()
    precision_obj.soot_class_hierarchy_precision()
    precision_obj.wala_class_hierarchy_precision()


def runner(analysis: str, benchmarks: List[str]) -> None:
    ir_results_soot = []
    ir_results_wala = []
    soot_cha_results = []
    wala_cha_results = []
    results_dir = Path(".") / "results"
    for b in benchmarks:
        print(f'\n\n{b}')
        ir_precision_soot_res = {'benchmark': b}
        ir_precision_wala_res = {'benchmark': b}
        soot_cha_precision_res = {'benchmark': b}
        wala_cha_precision_res = {'benchmark': b}

        precisions = ComputePrecision(analysis=analysis, benchmark=b)
        ir_precision_soot_res.update(precisions.soot_ir_precision())
        ir_precision_wala_res.update(precisions.wala_ir_precision())
        soot_cha_precision_res.update(precisions.soot_class_hierarchy_precision())
        wala_cha_precision_res.update(precisions.wala_class_hierarchy_precision())

        ir_results_soot.append(ir_precision_soot_res)
        ir_results_wala.append(ir_precision_wala_res)
        soot_cha_results.append(soot_cha_precision_res)
        wala_cha_results.append(wala_cha_precision_res)

    pretty_print_latex(ir_results_soot, str(results_dir / f"soot-ir-results-{analysis}.tex"))
    pretty_print_latex(ir_results_wala, str(results_dir / f"wala-ir-results-{analysis}.tex"))
    pretty_print_latex(soot_cha_results, str(results_dir / f"soot-cha-results-{analysis}.tex"))
    pretty_print_latex(wala_cha_results, str(results_dir / f"wala-cha-results-{analysis}.tex"))

    with open(results_dir / f"results_{analysis}.txt", "w") as op_file:
        op_file.write("\n~~~~~~~~~~~~~~~~~~~~~~~~ Soot IR Results ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        pretty_print_stats(ir_results_soot, op_file)
        op_file.write("\n~~~~~~~~~~~~~~~~~~~~~~~~ Wala IR Results ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        pretty_print_stats(ir_results_wala, op_file)
        op_file.write("\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~ Soot CHA Results ~~~~~~~~~~~~~~~~~~~~~~~~\n")
        pretty_print_stats(soot_cha_results, op_file)
        op_file.write("\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~ WALA CHA Results ~~~~~~~~~~~~~~~~~~~~~~~~\n")
        pretty_print_stats(wala_cha_results, op_file)

        pretty_print_csv(soot_cha_results, str(results_dir / f"soot-cha-results-{analysis}.csv"))
        pretty_print_csv(wala_cha_results, str(results_dir / f"wala-cha-results-{analysis}.csv"))
        pretty_print_csv(ir_results_soot, str(results_dir / f"soot-ir-results-{analysis}.csv"))
        pretty_print_csv(ir_results_wala, str(results_dir / f"wala-ir-results-{analysis}.csv"))

        print_wilcoxon_results(ir_results_soot, ('precision_ir', 'precision_actual'), "Soot IR Wilcoxon", op_file)
        print_wilcoxon_results(ir_results_wala, ('precision_ir', 'precision_actual'), "Wala IR Wilcoxon", op_file)
        print_wilcoxon_results(soot_cha_results, ('precision_prev', 'precision'), "Soot CHA Results", op_file)
        print_wilcoxon_results(wala_cha_results, ('precision_prev', 'precision'), "Wala CHA Results", op_file)


def compute_precision_1cs() -> None:
    print("Running 1cs")
    runner("1cs", BENCHMARKS)


def compute_precision_1os() -> None:
    print("Running 1os")
    runner("1os", BENCHMARKS)


def compute_precision_2cs() -> None:
    print("Running 2cs")
    benchmarks = BENCHMARKS.copy()
    benchmarks.remove('eclipse')
    benchmarks.remove('jython')
    runner("2cs", benchmarks)


def compute_precision_2os() -> None:
    print("Running 2os")
    benchmarks = BENCHMARKS.copy()
    benchmarks.remove('eclipse')
    benchmarks.remove('jython')
    runner("2os", benchmarks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("metrics compute")
    parser.add_argument('-a', choices=['1cs', '2cs', '1os', '2os', '1csheap'])
    parser.add_argument('-b', choices=BENCHMARKS)
    args = vars(parser.parse_args(sys.argv[1:]))
    has_benchmark = bool(args['b'])
    analysis_opt = args['a']
    if not has_benchmark:
        if analysis_opt == '1cs':
            compute_precision_1cs()
        elif analysis_opt == '1os':
            compute_precision_1os()
        elif analysis_opt == '2cs':
            compute_precision_2cs()
        elif analysis_opt == '2os':
            compute_precision_2os()
    else:
        runner_single_benchmark(analysis_opt, [args['b']])
