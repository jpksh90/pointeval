import logging

from varpointstodb import VarPointsToTable
from virtualcallvardb import VirtualCallVariablesTable
from exclusive_classes import exclusive_classes_wala
from exclusive_classes import exclusive_classes_soot
from utils import get_type_info
from utils import pp_dictionary
from virtual_call_stats import number_virtual_calls


def is_exclass_type(var, ex_class):
    col_idx = var.find(':')
    var_type = var[0:col_idx]
    if var_type in ex_class:
        return True
    return False


class ComputePrecision(object):
    """
    benchmark: string
        Benchmark name
    analysis: string
        analysis type (e.g. 1-call-site, 2-call-site, and others)
    """
    def __init__(self, benchmark, analysis):
        logging.basicConfig(filename='info.log', filemode='w', level=logging.INFO)
        self.analysis = analysis
        self.benchmark = benchmark
        self.soot_db = VarPointsToTable(benchmark=benchmark, analysis=analysis, ir='soot')
        self.wala_db = VarPointsToTable(benchmark=benchmark, analysis=analysis, ir='wala')
        wala_virtualcall_vars_db = VirtualCallVariablesTable(benchmark=benchmark, analysis=analysis, ir='wala')
        soot_virtualcall_vars_db = VirtualCallVariablesTable(benchmark=benchmark, analysis=analysis, ir='soot')
        self.wala_virtualcall_vars = wala_virtualcall_vars_db.virtualcall_variables()
        self.soot_virtualcall_vars = soot_virtualcall_vars_db.virtualcall_variables()
        self.interesting_types = set()
        logging.debug("soot db length", self.soot_db.db.__len__())
        logging.debug("wala db length", self.wala_db.db.__len__())

    def soot_must_alias(self):
        """
        computes the must alias information from the pointer analysis based on soot-framework
        :return:
        """
        print("Computing must-alias for all variables")
        return self.compute_must_must_alias(self.soot_db)

    def wala_must_alias(self):
        """
        computes the must alias analysis information from the pointer analysis based on wala-framework
        :return:
        """
        print("Computing must-alias for all variables")
        return self.compute_must_must_alias(self.wala_db)

    def _ir_precision(self, interesting_methods, db, virtual_call_vars, ir):
        """
        computes the precision for the invoking objects variables in the virtual method calls
        :param interesting_methods: checks if the number of variables in the methods having the same signature are different for different IRs
        :param db: target database, either soot or wala for now
        :param virtual_call_vars: invoking variables in the virtual methods calls
        :param ir: name of the ir
        :return: dictionary of the precision metrics
        """
        # check the interesting types
        _vars = db.variables_of_enclosed_method(tuple(interesting_methods))
        vars = self.select_virtualcall_variables(_vars, virtual_call_vars)
        rel_heap_objs = db.heap_objs_for_var(vars)
        # dump relevant heap objects
        dump_heap_info_to_file(self.benchmark+f"_{ir}.dump", rel_heap_objs)
        nb_virtual_calls = number_virtual_calls(analysis=self.analysis, benchmark=self.benchmark, ir=ir)
        precision_ir = len(rel_heap_objs) / nb_virtual_calls
        total_heap_objs = db.all_heap_ctx_pair()
        total_vars = db.all_variables_ctx_pair()
        precision_actual = len(total_heap_objs) / len(total_vars) if len(total_vars) != 0 else 0
        return dict(interesting_types=len(interesting_methods), relevant_vars=len(vars),
                    relevant_heap_objects=len(rel_heap_objs), vars=len(total_vars), heap_objects=len(total_heap_objs),
                    precision_ir=precision_ir, precision_actual=precision_actual, nb_virtual_calls=nb_virtual_calls)

    def _compute_interesting_methods(self):
        """
        computes the interesting methods. A method is interesting if the number of variables in the methods having the same signature are different for different IRs
        :return:
        """
        ex_class_soot = exclusive_classes_soot(self.benchmark)
        ex_class_wala = exclusive_classes_wala(self.benchmark)

        soot_var_methods = self.soot_db.get_var_enclosing_method()
        _soot_var_methods = soot_var_methods.copy()
        for v in _soot_var_methods:  # remove the interference from class hierarchy
            if is_exclass_type(v, ex_class_soot):
                soot_var_methods.remove(v)

        wala_var_methods = self.wala_db.get_var_enclosing_method()
        _wala_var_methods = wala_var_methods.copy()
        for v in _wala_var_methods:  # remove the intereference from class hierarchy
            if is_exclass_type(v, ex_class_wala):
                wala_var_methods.remove(v)

        types_union = soot_var_methods.intersection(wala_var_methods)
        soot_vars_for_type = self.soot_db.count_nb_of_variables_method()
        wala_vars_for_type = self.wala_db.count_nb_of_variables_method()

        # filter out the exclusive classes
        for t in types_union:
            soot_vars_cnt = soot_vars_for_type[t] if t in soot_vars_for_type else 0
            wala_vars_cnt = wala_vars_for_type[t] if t in wala_vars_for_type else 0
            if soot_vars_cnt != wala_vars_cnt:
                self.interesting_types.add(t)
        print(
            f"soot var methods = {len(soot_var_methods)}; wala var methods = {len(wala_var_methods)}; "
            f"interesting types = {len(self.interesting_types)}")

        fh = open(f"logs/soot_{self.analysis}_{self.benchmark}_var_types.log", 'w+')
        for k, v in soot_vars_for_type.items():
            fh.write(f"{k}:{v}\n")
        fh = open(f"logs/wala_{self.analysis}_{self.benchmark}_var_types.log", 'w+')
        for k, v in wala_vars_for_type.items():
            fh.write(f"{k}:{v}\n")

    def resolve_interesting_types(self):
        """
        prevents redundant calls to database by caching the set of interesting methods
        :return:
        """
        if len(self.interesting_types) == 0:
            self._compute_interesting_methods()

    def soot_ir_precision(self):
        """
        Computes the precision for soot IR. This is the API function which is exposed to outside classes.
        :return:
        """
        self.resolve_interesting_types()
        res = self._ir_precision(self.interesting_types, self.soot_db, self.soot_virtualcall_vars, "soot")
        print('----------------------------- Soot IR Precision -----------------------------------------')
        print(f"benchmark = {self.benchmark}, analysis = {self.analysis}")
        pp_dictionary(res)
        return res

    def wala_ir_precision(self):
        """
        Computes the precision for wala IR. This is the API function which is exposed to outside classes.
        :return:
        """
        self.resolve_interesting_types()
        res = self._ir_precision(self.interesting_types, self.wala_db, self.wala_virtualcall_vars, "wala")
        print('----------------------------- Wala IR Precision -----------------------------------------')
        print(f"benchmark = {self.benchmark}, analysis = {self.analysis}")
        pp_dictionary(res)
        return res

    def select_virtualcall_variables(self, vars, virtualcall_vars):
        """
        Selects the invoking variables at the virtual calls. The variables are kept as (varCtx, var) pairs where varCtx is the context-information (calling or object) of the variable var.
        :param vars: list of (varCtx, var) pairs
        :param virtualcall_vars: list of variables
        :return:
        """
        res_vars = set()
        for v in vars:
            if v[1] in virtualcall_vars:
                res_vars.add(v)
        return res_vars

    def class_hierarchy_precision(self, ex_types, db, virtualcall_vars):
        """
        Computes the class hierarchy precision (CH-precision)
        :param virtualcall_vars:
        :param ir: compute the class hierarchy
        :param db: var points-to database
        :return: a dictionary of (ex_vars, ex_heap_objs, heap_objs, variables, precision)
        """
        # get the number of exclusive variables and heap objects
        _ex_vars = db.variables_by_enclosed_method_class(tuple(ex_types))
        # choose the variable in virtual calls
        ex_vars = self.select_virtualcall_variables(_ex_vars, virtualcall_vars)
        ex_heapObjs = db.heap_objs_for_var(ex_vars)

        _all_vars = db.all_variables_ctx_pair()
        variables = self.select_virtualcall_variables(_all_vars, virtualcall_vars)
        heap_objs = db.heap_objs_for_var(variables)
        precision_prev = len(heap_objs) / len(variables) if len(variables) != 0 else 0
        if ex_heapObjs is None:
            ex_heapObjs = []
        if ex_vars is None:
            ex_vars = []
        # compute the type for exclusive vars
        ex_vars_types = set(map(lambda x: get_type_info(x), [v[1] for v in ex_vars]))
        precision = (len(heap_objs) - len(ex_heapObjs)) / (len(variables) - len(ex_vars)) if (len(variables) - len(
            ex_vars)) != 0 else 0
        results = {'ex_type': len(ex_types), 'ex_vars': len(ex_vars), 'ex_heap_objs': len(ex_heapObjs),
                   'heap_objs': len(heap_objs), 'variables': len(variables), 'precision': precision,
                   'precision_prev': precision_prev, 'ex_vars_types': ex_vars_types}
        # print(self.benchmark, ex_vars)
        return results

    def soot_class_hierarchy_precision(self):
        ex_types = exclusive_classes_soot(self.benchmark)
        res = self.class_hierarchy_precision(ex_types, self.soot_db, self.soot_virtualcall_vars)
        print("=============== SOOT CLASS HIERARCHY PRECISION =========================")
        pp_dictionary(res)
        return res

    def wala_class_hierarchy_precision(self):
        ex_types = exclusive_classes_wala(self.benchmark)
        res = self.class_hierarchy_precision(ex_types, self.wala_db, self.wala_virtualcall_vars)
        print("=============== WALA CLASS HIERARCHY PRECISION =========================")
        pp_dictionary(res)
        return res


def dump_heap_info_to_file(filename, list_of_heap_objs):
    #convert the list of a set
    set_of_heap_objs = set(list_of_heap_objs)
    with open(filename, 'w+') as fh:
        for l in set_of_heap_objs:
            fh.write(str(l) + '\n')
            # fh.write(f'{l[0]}\t{l[1]}')
            # fh.write('\n')
