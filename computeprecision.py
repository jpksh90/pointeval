import logging
from typing import Dict, Set, Tuple, Any, List, Optional

from varpointstodb import VarPointsToTable
from virtualcallvardb import VirtualCallVariablesTable
from exclusive_classes import exclusive_classes_wala, exclusive_classes_soot
from utils import get_type_info, pp_dictionary
from virtual_call_stats import number_virtual_calls


def is_exclass_type(var: str, ex_class: Set[str]) -> bool:
    col_idx = var.find(':')
    var_type = var[0:col_idx]
    return var_type in ex_class


class ComputePrecision:
    """
    Compute precision metrics for pointer analysis.

    Parameters
    ----------
    benchmark : str
        Benchmark name
    analysis : str
        Analysis type (e.g. 1-call-site, 2-call-site, and others)
    """
    def __init__(self, benchmark: str, analysis: str) -> None:
        logging.basicConfig(filename='info.log', filemode='w', level=logging.INFO)
        self.analysis = analysis
        self.benchmark = benchmark
        self.soot_db = VarPointsToTable(benchmark=benchmark, analysis=analysis, ir='soot')
        self.wala_db = VarPointsToTable(benchmark=benchmark, analysis=analysis, ir='wala')
        wala_virtualcall_vars_db = VirtualCallVariablesTable(benchmark=benchmark, analysis=analysis, ir='wala')
        soot_virtualcall_vars_db = VirtualCallVariablesTable(benchmark=benchmark, analysis=analysis, ir='soot')
        self.wala_virtualcall_vars = wala_virtualcall_vars_db.virtualcall_variables()
        self.soot_virtualcall_vars = soot_virtualcall_vars_db.virtualcall_variables()
        self.interesting_types: Set[str] = set()
        logging.debug("soot db length", self.soot_db.db.__len__())
        logging.debug("wala db length", self.wala_db.db.__len__())

    def soot_must_alias(self) -> Any:
        """Compute must-alias information from soot pointer analysis."""
        print("Computing must-alias for all variables")
        return self.compute_must_must_alias(self.soot_db)

    def wala_must_alias(self) -> Any:
        """Compute must-alias information from wala pointer analysis."""
        print("Computing must-alias for all variables")
        return self.compute_must_must_alias(self.wala_db)

    def _ir_precision(
        self,
        interesting_methods: Set[str],
        db: VarPointsToTable,
        virtual_call_vars: Set[str],
        ir: str,
    ) -> Dict[str, Any]:
        """
        Compute precision for invoking objects variables in virtual method calls.

        Parameters
        ----------
        interesting_methods : Set[str]
            Methods with different variable counts across IRs
        db : VarPointsToTable
            Target database (soot or wala)
        virtual_call_vars : Set[str]
            Invoking variables in virtual method calls
        ir : str
            IR name

        Returns
        -------
        Dict[str, Any]
            Dictionary of precision metrics
        """
        _vars = db.variables_of_enclosed_method(tuple(interesting_methods))
        vars = self.select_virtualcall_variables(_vars, virtual_call_vars)
        rel_heap_objs = db.heap_objs_for_var(vars)
        dump_heap_info_to_file(f"{self.benchmark}_{ir}.dump", rel_heap_objs)
        nb_virtual_calls = number_virtual_calls(analysis=self.analysis, benchmark=self.benchmark, ir=ir)
        precision_ir = len(rel_heap_objs) / nb_virtual_calls
        total_heap_objs = db.all_heap_ctx_pair()
        total_vars = db.all_variables_ctx_pair()
        precision_actual = len(total_heap_objs) / len(total_vars) if len(total_vars) != 0 else 0
        return {
            'interesting_types': len(interesting_methods),
            'relevant_vars': len(vars),
            'relevant_heap_objects': len(rel_heap_objs),
            'vars': len(total_vars),
            'heap_objects': len(total_heap_objs),
            'precision_ir': precision_ir,
            'precision_actual': precision_actual,
            'nb_virtual_calls': nb_virtual_calls,
        }

    def _compute_interesting_methods(self) -> None:
        """Compute interesting methods with different variable counts across IRs."""
        ex_class_soot = exclusive_classes_soot(self.benchmark)
        ex_class_wala = exclusive_classes_wala(self.benchmark)

        soot_var_methods = self.soot_db.get_var_enclosing_method()
        _soot_var_methods = soot_var_methods.copy()
        for v in _soot_var_methods:
            if is_exclass_type(v, ex_class_soot):
                soot_var_methods.remove(v)

        wala_var_methods = self.wala_db.get_var_enclosing_method()
        _wala_var_methods = wala_var_methods.copy()
        for v in _wala_var_methods:
            if is_exclass_type(v, ex_class_wala):
                wala_var_methods.remove(v)

        types_union = soot_var_methods.intersection(wala_var_methods)
        soot_vars_for_type = self.soot_db.count_nb_of_variables_method()
        wala_vars_for_type = self.wala_db.count_nb_of_variables_method()

        for t in types_union:
            soot_vars_cnt = soot_vars_for_type.get(t, 0)
            wala_vars_cnt = wala_vars_for_type.get(t, 0)
            if soot_vars_cnt != wala_vars_cnt:
                self.interesting_types.add(t)
        print(
            f"soot var methods = {len(soot_var_methods)}; wala var methods = {len(wala_var_methods)}; "
            f"interesting types = {len(self.interesting_types)}")

        with open(f"logs/soot_{self.analysis}_{self.benchmark}_var_types.log", 'w+') as fh:
            for k, v in soot_vars_for_type.items():
                fh.write(f"{k}:{v}\n")
        with open(f"logs/wala_{self.analysis}_{self.benchmark}_var_types.log", 'w+') as fh:
            for k, v in wala_vars_for_type.items():
                fh.write(f"{k}:{v}\n")

    def resolve_interesting_types(self) -> None:
        """Cache set of interesting methods to prevent redundant database calls."""
        if len(self.interesting_types) == 0:
            self._compute_interesting_methods()

    def soot_ir_precision(self) -> Dict[str, Any]:
        """Compute precision for soot IR."""
        self.resolve_interesting_types()
        res = self._ir_precision(self.interesting_types, self.soot_db, self.soot_virtualcall_vars, "soot")
        print('----------------------------- Soot IR Precision -----------------------------------------')
        print(f"benchmark = {self.benchmark}, analysis = {self.analysis}")
        pp_dictionary(res)
        return res

    def wala_ir_precision(self) -> Dict[str, Any]:
        """Compute precision for wala IR."""
        self.resolve_interesting_types()
        res = self._ir_precision(self.interesting_types, self.wala_db, self.wala_virtualcall_vars, "wala")
        print('----------------------------- Wala IR Precision -----------------------------------------')
        print(f"benchmark = {self.benchmark}, analysis = {self.analysis}")
        pp_dictionary(res)
        return res

    def select_virtualcall_variables(
        self,
        vars: Set[Tuple[str, str]],
        virtualcall_vars: Set[str],
    ) -> Set[Tuple[str, str]]:
        """Select invoking variables at virtual calls."""
        return {v for v in vars if v[1] in virtualcall_vars}

    def class_hierarchy_precision(
        self,
        ex_types: Set[str],
        db: VarPointsToTable,
        virtualcall_vars: Set[str],
    ) -> Dict[str, Any]:
        """
        Compute class hierarchy precision (CH-precision).

        Parameters
        ----------
        ex_types : Set[str]
            Exclusive types
        db : VarPointsToTable
            Variable points-to database
        virtualcall_vars : Set[str]
            Variables in virtual calls

        Returns
        -------
        Dict[str, Any]
            Dictionary with precision metrics
        """
        _ex_vars = db.variables_by_enclosed_method_class(tuple(ex_types))
        ex_vars = self.select_virtualcall_variables(_ex_vars, virtualcall_vars)
        ex_heap_objs = db.heap_objs_for_var(ex_vars)

        _all_vars = db.all_variables_ctx_pair()
        variables = self.select_virtualcall_variables(_all_vars, virtualcall_vars)
        heap_objs = db.heap_objs_for_var(variables)
        precision_prev = len(heap_objs) / len(variables) if len(variables) != 0 else 0
        if ex_heap_objs is None:
            ex_heap_objs = []
        if ex_vars is None:
            ex_vars = []
        ex_vars_types = {get_type_info(v[1]) for v in ex_vars}
        precision = (
            (len(heap_objs) - len(ex_heap_objs)) / (len(variables) - len(ex_vars))
            if (len(variables) - len(ex_vars)) != 0
            else 0
        )
        return {
            'ex_type': len(ex_types),
            'ex_vars': len(ex_vars),
            'ex_heap_objs': len(ex_heap_objs),
            'heap_objs': len(heap_objs),
            'variables': len(variables),
            'precision': precision,
            'precision_prev': precision_prev,
            'ex_vars_types': ex_vars_types,
        }

    def soot_class_hierarchy_precision(self) -> Dict[str, Any]:
        ex_types = exclusive_classes_soot(self.benchmark)
        res = self.class_hierarchy_precision(ex_types, self.soot_db, self.soot_virtualcall_vars)
        print("=============== SOOT CLASS HIERARCHY PRECISION =========================")
        pp_dictionary(res)
        return res

    def wala_class_hierarchy_precision(self) -> Dict[str, Any]:
        ex_types = exclusive_classes_wala(self.benchmark)
        res = self.class_hierarchy_precision(ex_types, self.wala_db, self.wala_virtualcall_vars)
        print("=============== WALA CLASS HIERARCHY PRECISION =========================")
        pp_dictionary(res)
        return res


def dump_heap_info_to_file(filename: str, list_of_heap_objs: List[Tuple[str, str]]) -> None:
    """Write unique heap objects to a file."""
    set_of_heap_objs = set(list_of_heap_objs)
    with open(filename, 'w+') as fh:
        for heap_obj in set_of_heap_objs:
            fh.write(f'{heap_obj}\n')
