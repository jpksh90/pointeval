import os
import argparse
import sys

BENCHMARKS = ['avrora', 'batik', 'eclipse', 'h2', 'jython', 'lusearch', 'luindex', 'pmd', 'sunflow', 'tradebeans',
              'xalan']

from computeprecision import ComputePrecision
from utils import pretty_print_csv
from utils import pretty_print_latex
from utils import pretty_print_stats
from utils import print_wilcoxon_results


def runner_single_benchmark(analysis, benchmark):
    print("analysis= ", analysis, "benchmark= ", benchmark)
    precison = ComputePrecision(analysis=analysis, benchmark=benchmark[0])
    precison.wala_ir_precision()
    precison.soot_ir_precision()
    precison.soot_class_hierarchy_precision()
    precison.wala_class_hierarchy_precision()


def runner(analysis, benchmarks):
    ir_results_soot = []
    ir_results_wala = []
    soot_cha_results = []
    wala_cha_results = []
    for b in benchmarks:
        print('\n', '\n', b)
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

    # output latex files
    pretty_print_latex(ir_results_soot, os.path.join(".", "results", f"soot-ir-results-{analysis}.tex"))
    pretty_print_latex(ir_results_wala, os.path.join(".", "results", f"wala-ir-results-{analysis}.tex"))
    pretty_print_latex(soot_cha_results, os.path.join(".", "results", f"soot-cha-results-{analysis}.tex"))
    pretty_print_latex(wala_cha_results, os.path.join(".", "results", f"wala-cha-results-{analysis}.tex"))

    # Print to txt file
    op_file = open(os.path.join(".", "results", f"results_{analysis}.txt"), "w")
    op_file.write("\n~~~~~~~~~~~~~~~~~~~~~~~~ Soot IR Results ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    pretty_print_stats(ir_results_soot, op_file)
    op_file.write("\n~~~~~~~~~~~~~~~~~~~~~~~~ Wala IR Results ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    pretty_print_stats(ir_results_wala, op_file)
    op_file.write("\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~ Soot CHA Results ~~~~~~~~~~~~~~~~~~~~~~~~\n")
    pretty_print_stats(soot_cha_results, op_file)
    op_file.write("\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~ WALA CHA Results ~~~~~~~~~~~~~~~~~~~~~~~~\n")
    pretty_print_stats(wala_cha_results, op_file)

    # print to csv files for excellent graph plotting
    pretty_print_csv(soot_cha_results, os.path.join(".", "results", f"soot-cha-results-{analysis}.csv"))
    pretty_print_csv(wala_cha_results, os.path.join(".", "results", f"wala-cha-results-{analysis}.csv"))
    pretty_print_csv(ir_results_soot, os.path.join(".", "results", f"soot-ir-results-{analysis}.csv"))
    pretty_print_csv(ir_results_wala, os.path.join(".", "results", f"wala-ir-results-{analysis}.csv"))

    # compute the wilcoxson-pratt t-test for IR resuls
    print_wilcoxon_results(ir_results_soot, ('precision_ir', 'precision_actual'), "Soot IR Wilcoxon", op_file)
    print_wilcoxon_results(ir_results_wala, ('precision_ir', 'precision_actual'), "Wala IR Wilcoxon", op_file)
    print_wilcoxon_results(soot_cha_results, ('precision_prev', 'precision'), "Soot CHA Results", op_file)
    print_wilcoxon_results(wala_cha_results, ('precision_prev', 'precision'), "Wala CHA Results", op_file)
    op_file.close()


def compute_precision_1cs():
    print("Running 1cs")
    runner("1cs", BENCHMARKS)


def compute_precision_1os():
    print("Running 1os")
    runner("1os", BENCHMARKS)


def compute_precision_2cs():
    print("Running 2cs")
    benchmarks = BENCHMARKS
    # These analysis did not terminate within time budget
    benchmarks.remove('eclipse')
    benchmarks.remove('jython')
    runner("2cs", benchmarks)


def compute_precision_2os():
    print("Running 2os")
    benchmarks = BENCHMARKS
    # These analysis did not terminate within time budget
    benchmarks.remove('eclipse')
    benchmarks.remove('jython')
    runner("2os", benchmarks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("metrics compute")
    parser.add_argument('-a', choices=['1cs', '2cs', '1os', '2os', '1csheap'])
    parser.add_argument('-b', choices=BENCHMARKS)
    args = vars(parser.parse_args(sys.argv[1:]))
    hasB = True if args['b'] else False
    analysis_opt = args['a']
    if not hasB:
        if analysis_opt == '1cs':
            compute_precision_1cs()
        elif analysis_opt == '1os':
            compute_precision_1os()
        elif analysis_opt == '2cs':
            compute_precision_2cs()
        elif analysis_opt == '2os':
            compute_precision_2os()
    elif hasB:
        runner_single_benchmark(analysis_opt, [args['b']])
    else:
        sys.exit(128)
