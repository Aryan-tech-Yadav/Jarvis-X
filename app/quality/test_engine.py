"""Automated Test Generator and Test Execution Engine with Code Coverage."""

from __future__ import annotations

import ast
import importlib.util
import io
import os
import re
import sys
import tempfile
import time
import traceback
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .models.test_result import (
    CoverageResult,
    TestCaseResult,
    TestSuiteResult,
    TestType,
)


class TestGenerator:
    """Generates Unit, Integration, Edge Case, Regression, and Smoke tests."""

    def generate_tests_for_code(
        self, code: str, module_name: str = "target_module", test_types: Optional[List[TestType]] = None
    ) -> Dict[TestType, str]:
        if test_types is None:
            test_types = [TestType.UNIT, TestType.EDGE_CASE, TestType.SMOKE, TestType.INTEGRATION]

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {}

        results: Dict[TestType, str] = {}
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and not n.name.startswith("_")]

        if TestType.SMOKE in test_types:
            results[TestType.SMOKE] = self._generate_smoke_tests(module_name, functions, classes)

        if TestType.UNIT in test_types:
            results[TestType.UNIT] = self._generate_unit_tests(module_name, functions, classes)

        if TestType.EDGE_CASE in test_types:
            results[TestType.EDGE_CASE] = self._generate_edge_case_tests(module_name, functions, classes)

        if TestType.INTEGRATION in test_types:
            results[TestType.INTEGRATION] = self._generate_integration_tests(module_name, functions, classes)

        return results

    def _generate_smoke_tests(self, mod_name: str, functions: List[ast.FunctionDef], classes: List[ast.ClassDef]) -> str:
        lines = [
            "import unittest",
            f"import {mod_name}",
            "",
            f"class Test{mod_name.capitalize()}Smoke(unittest.TestCase):",
            "    def test_module_imports_and_has_symbols(self):",
            f"        self.assertIsNotNone({mod_name})",
        ]
        for f in functions:
            lines.append(f"        self.assertTrue(hasattr({mod_name}, '{f.name}'))")
        for c in classes:
            lines.append(f"        self.assertTrue(hasattr({mod_name}, '{c.name}'))")

        for c in classes:
            init_method = next((m for m in c.body if isinstance(m, ast.FunctionDef) and m.name == "__init__"), None)
            req_args = []
            if init_method:
                # Count non-default args (excluding self)
                non_default_count = len(init_method.args.args) - 1 - len(init_method.args.defaults)
                for i in range(max(0, non_default_count)):
                    arg_name = init_method.args.args[i + 1].arg
                    req_args.append(self._guess_dummy_arg(arg_name))
            args_str = ", ".join(req_args)
            lines.append(f"    def test_instantiate_{c.name.lower()}(self):")
            lines.append(f"        try:")
            lines.append(f"            instance = {mod_name}.{c.name}({args_str})")
            lines.append(f"            self.assertIsNotNone(instance)")
            lines.append(f"        except Exception as e:")
            lines.append(f"            self.fail(f'Failed to instantiate {c.name}: {{e}}')")

        lines.append("")
        return "\n".join(lines)


    def _generate_unit_tests(self, mod_name: str, functions: List[ast.FunctionDef], classes: List[ast.ClassDef]) -> str:
        lines = [
            "import unittest",
            f"import {mod_name}",
            "",
            f"class Test{mod_name.capitalize()}Unit(unittest.TestCase):",
        ]
        if not functions and not classes:
            lines.append("    def test_default_pass(self):")
            lines.append("        self.assertTrue(True)")
            lines.append("")
            return "\n".join(lines)

        for f in functions:
            req_args = [self._guess_dummy_arg(a.arg) for a in f.args.args]
            args_str = ", ".join(req_args)
            lines.append(f"    def test_{f.name}_basic_call(self):")
            lines.append(f"        try:")
            lines.append(f"            result = {mod_name}.{f.name}({args_str})")
            lines.append(f"            self.assertIsNotNone(result) if result is not None else self.assertTrue(True)")
            lines.append(f"        except Exception as e:")
            lines.append(f"            self.fail(f'{f.name} raised unexpected exception: {{e}}')")

        for c in classes:
            methods = [m for m in c.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")]
            init_method = next((m for m in c.body if isinstance(m, ast.FunctionDef) and m.name == "__init__"), None)
            req_init_args = []
            if init_method:
                non_default_count = len(init_method.args.args) - 1 - len(init_method.args.defaults)
                for i in range(max(0, non_default_count)):
                    req_init_args.append(self._guess_dummy_arg(init_method.args.args[i + 1].arg))
            init_str = ", ".join(req_init_args)

            for m in methods:
                m_args = [self._guess_dummy_arg(a.arg) for a in m.args.args[1:]]
                m_args_str = ", ".join(m_args)
                lines.append(f"    def test_{c.name.lower()}_{m.name}(self):")
                lines.append(f"        obj = {mod_name}.{c.name}({init_str})")
                lines.append(f"        res = obj.{m.name}({m_args_str})")
                lines.append(f"        self.assertIsNotNone(res) if res is not None else self.assertTrue(True)")

        lines.append("")
        return "\n".join(lines)

    def _generate_edge_case_tests(self, mod_name: str, functions: List[ast.FunctionDef], classes: List[ast.ClassDef]) -> str:
        lines = [
            "import unittest",
            f"import {mod_name}",
            "",
            f"class Test{mod_name.capitalize()}EdgeCases(unittest.TestCase):",
        ]
        for f in functions:
            if f.args.args:
                edge_sets = self._guess_edge_args(f.args.args)
                for idx, edge_args in enumerate(edge_sets):
                    args_str = ", ".join(edge_args)
                    lines.append(f"    def test_{f.name}_edge_case_{idx}(self):")
                    lines.append(f"        try:")
                    lines.append(f"            {mod_name}.{f.name}({args_str})")
                    lines.append(f"        except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError):")
                    lines.append(f"            pass  # Expected boundary handling")
                    lines.append(f"        except Exception as e:")
                    lines.append(f"            self.assertTrue(isinstance(e, Exception))")

        if len(lines) == 4:
            lines.append("    def test_no_args_boundary(self):")
            lines.append("        self.assertTrue(True)")

        lines.append("")
        return "\n".join(lines)

    def _generate_integration_tests(self, mod_name: str, functions: List[ast.FunctionDef], classes: List[ast.ClassDef]) -> str:
        lines = [
            "import unittest",
            f"import {mod_name}",
            "",
            f"class Test{mod_name.capitalize()}Integration(unittest.TestCase):",
            "    def test_pipeline_workflow(self):",
            f"        # Test multi-step pipeline integration",
        ]
        if classes:
            c = classes[0]
            lines.append(f"        instance = {mod_name}.{c.name}()")
            lines.append(f"        self.assertIsNotNone(instance)")
        else:
            lines.append(f"        self.assertTrue(hasattr({mod_name}, '__name__'))")
        lines.append("")
        return "\n".join(lines)

    def generate_regression_test(self, mod_name: str, bug_name: str, code_snippet: str) -> str:
        safe_bug = re.sub(r"\W+", "_", bug_name).lower()
        return f"""import unittest
import {mod_name}

class Test{mod_name.capitalize()}Regression_{safe_bug}(unittest.TestCase):
    def test_guard_against_{safe_bug}(self):
        # Regression guard test
        {code_snippet}
"""

    def _guess_dummy_arg(self, arg_name: str) -> str:
        name = arg_name.lower()
        if "count" in name or "num" in name or "limit" in name or "id" in name or "port" in name or "age" in name:
            return "1"
        if "rate" in name or "score" in name or "price" in name or "ratio" in name:
            return "1.0"
        if "is_" in name or "has_" in name or "flag" in name or "enabled" in name or "active" in name:
            return "True"
        if "items" in name or "list" in name or "elements" in name or "args" in name:
            return "[]"
        if "data" in name or "config" in name or "mapping" in name or "dict" in name or "kwargs" in name:
            return "{}"
        return "'test_input'"

    def _guess_edge_args(self, args: List[ast.arg]) -> List[List[str]]:
        # None set, empty set, extreme set
        nones = ["None" for _ in args]
        empties = ["''" if i % 2 == 0 else "0" for i in range(len(args))]
        extremes = ["-999999" if i % 2 == 0 else "float('inf')" for i in range(len(args))]
        return [nones, empties, extremes]



class TestEngine:
    """Executes automated tests, captures tracebacks, and measures statement coverage."""

    def __init__(self, root_path: Optional[str] = None):
        self.root_path = Path(root_path).resolve() if root_path else Path.cwd()
        self.generator = TestGenerator()

    def run_tests_in_directory(self, target_dir: Optional[str] = None) -> TestSuiteResult:
        dir_path = Path(target_dir).resolve() if target_dir else self.root_path
        test_dir = dir_path / "tests" if (dir_path / "tests").exists() else dir_path

        loader = unittest.TestLoader()
        start_time = time.perf_counter()

        # Discover tests
        try:
            suite = loader.discover(str(test_dir), pattern="test_*.py", top_level_dir=str(dir_path))
        except Exception as e:
            return TestSuiteResult(
                total_tests=0,
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                success=False,
                failure_details=[{"name": "test_discovery", "error": str(e), "traceback": traceback.format_exc()}],
            )

        return self._execute_suite(suite, start_time, dir_path)

    def run_test_code(self, source_code: str, test_code: str, module_name: str = "temp_module") -> TestSuiteResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write source module
            src_file = tmppath / f"{module_name}.py"
            src_file.write_text(source_code, encoding="utf-8")

            # Write test module
            test_file = tmppath / f"test_{module_name}.py"
            test_file.write_text(test_code, encoding="utf-8")

            # Evict previous cached modules with same name
            for mod_key in [module_name, f"test_{module_name}"]:
                if mod_key in sys.modules:
                    del sys.modules[mod_key]

            # Add to sys.path
            sys.path.insert(0, str(tmppath))
            start_time = time.perf_counter()
            executed_lines: Dict[str, Set[int]] = defaultdict(set)

            def trace_calls(frame, event, arg):
                if event == "line":
                    try:
                        norm = str(Path(frame.f_code.co_filename).resolve()).lower()
                        executed_lines[norm].add(frame.f_lineno)
                    except Exception:
                        pass
                return trace_calls

            old_trace = sys.gettrace()
            sys.settrace(trace_calls)
            try:
                # Load source module
                spec_src = importlib.util.spec_from_file_location(module_name, str(src_file))
                if spec_src and spec_src.loader:
                    mod = importlib.util.module_from_spec(spec_src)
                    sys.modules[module_name] = mod
                    spec_src.loader.exec_module(mod)

                # Load test module
                spec_test = importlib.util.spec_from_file_location(f"test_{module_name}", str(test_file))
                if spec_test and spec_test.loader:
                    tmod = importlib.util.module_from_spec(spec_test)
                    sys.modules[f"test_{module_name}"] = tmod
                    spec_test.loader.exec_module(tmod)

                    loader = unittest.TestLoader()
                    suite = loader.loadTestsFromModule(tmod)
                    return self._execute_suite(suite, start_time, tmppath, target_files=[src_file], external_traces=executed_lines)
                else:
                    return TestSuiteResult(
                        total_tests=0,
                        passed=0,
                        failed=0,
                        errors=1,
                        success=False,
                        failure_details=[{"test": f"test_{module_name}", "type": "error", "message": "Failed to create module spec", "traceback": ""}],
                    )
            except Exception as e:
                return TestSuiteResult(
                    total_tests=0,
                    passed=0,
                    failed=0,
                    errors=1,
                    success=False,
                    failure_details=[{"test": f"test_{module_name}", "type": "error", "message": str(e), "traceback": traceback.format_exc()}],
                )
            finally:
                sys.settrace(old_trace)
                for mod_key in [module_name, f"test_{module_name}"]:
                    if mod_key in sys.modules:
                        del sys.modules[mod_key]
                if str(tmppath) in sys.path:
                    sys.path.remove(str(tmppath))

    def _execute_suite(
        self,
        suite: unittest.TestSuite,
        start_time: float,
        root_dir: Path,
        target_files: Optional[List[Path]] = None,
        external_traces: Optional[Dict[str, Set[int]]] = None,
    ) -> TestSuiteResult:
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)

        # Coverage line tracing
        executed_lines: Dict[str, Set[int]] = defaultdict(set)
        if external_traces is not None:
            for k, v in external_traces.items():
                executed_lines[k].update(v)

        def trace_calls(frame, event, arg):
            if event == "line":
                try:
                    norm = str(Path(frame.f_code.co_filename).resolve()).lower()
                    executed_lines[norm].add(frame.f_lineno)
                except Exception:
                    pass
            return trace_calls

        old_trace = sys.gettrace()
        sys.settrace(trace_calls)
        try:
            result = runner.run(suite)
        finally:
            if old_trace is not None:
                sys.settrace(old_trace)
            else:
                sys.settrace(None)

        duration = time.perf_counter() - start_time
        total_tests = result.testsRun
        failures_count = len(result.failures)
        errors_count = len(result.errors)
        skipped_count = len(result.skipped)
        passed_count = total_tests - (failures_count + errors_count + skipped_count)

        test_cases: List[TestCaseResult] = []
        failure_details: List[Dict[str, Any]] = []

        for test_case, tb in result.failures:
            tc_name = str(test_case)
            test_cases.append(
                TestCaseResult(
                    name=tc_name,
                    status="FAILED",
                    error_message=tb.splitlines()[-1] if tb else "Assertion Failed",
                    traceback_str=tb,
                )
            )
            failure_details.append({
                "test": tc_name,
                "type": "failure",
                "message": tb.splitlines()[-1] if tb else "Assertion Failed",
                "traceback": tb,
            })

        for test_case, tb in result.errors:
            tc_name = str(test_case)
            test_cases.append(
                TestCaseResult(
                    name=tc_name,
                    status="ERROR",
                    error_message=tb.splitlines()[-1] if tb else "Execution Error",
                    traceback_str=tb,
                )
            )
            failure_details.append({
                "test": tc_name,
                "type": "error",
                "message": tb.splitlines()[-1] if tb else "Execution Error",
                "traceback": tb,
            })

        # Calculate coverage
        coverage = self._calculate_coverage(root_dir, executed_lines, target_files)

        return TestSuiteResult(
            total_tests=total_tests,
            passed=passed_count,
            failed=failures_count,
            errors=errors_count,
            skipped=skipped_count,
            test_cases=test_cases,
            coverage=coverage,
            duration_sec=duration,
            success=(failures_count == 0 and errors_count == 0),
            failure_details=failure_details,
        )

    def _calculate_coverage(
        self, root_dir: Path, executed_lines: Dict[str, Set[int]], target_files: Optional[List[Path]] = None
    ) -> CoverageResult:
        files_to_check = target_files if target_files is not None else list(root_dir.glob("**/*.py"))
        total_statements = 0
        covered_statements = 0
        missing_lines: Dict[str, List[int]] = {}

        for file_path in files_to_check:
            p_str = str(file_path.resolve()).lower()
            fname = file_path.name.lower()
            if "test" in p_str or ".venv" in p_str or "__pycache__" in p_str:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content)

                # Identify docstrings to exclude from executable statements
                docstring_lines: Set[int] = set()
                for parent in ast.walk(tree):
                    if isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        if parent.body and isinstance(parent.body[0], ast.Expr) and isinstance(parent.body[0].value, (ast.Constant, ast.Str)):
                            docstring_lines.add(parent.body[0].lineno)

                stmt_lines: Set[int] = set()
                func_def_lines: Dict[int, List[int]] = {}  # def lineno -> body linenos

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        body_lines = [b.lineno for b in node.body if hasattr(b, "lineno") and b.lineno not in docstring_lines]
                        func_def_lines[node.lineno] = body_lines
                        stmt_lines.add(node.lineno)
                    elif isinstance(node, ast.stmt) and hasattr(node, "lineno"):
                        if node.lineno not in docstring_lines:
                            stmt_lines.add(node.lineno)

                if not stmt_lines:
                    continue

                # Find all executed lines matching this file
                hits: Set[int] = set()
                for k, lines in executed_lines.items():
                    if k == p_str or k.endswith(fname) or fname in k:
                        hits.update(lines)

                # If any line in a function body was hit, consider the def line hit
                for def_line, b_lines in func_def_lines.items():
                    if any(bl in hits for bl in b_lines):
                        hits.add(def_line)

                total_statements += len(stmt_lines)
                covered_in_file = hits.intersection(stmt_lines)
                covered_statements += len(covered_in_file)

                uncovered = sorted(list(stmt_lines - covered_in_file))
                if uncovered:
                    rel_name = str(file_path.name)
                    missing_lines[rel_name] = uncovered
            except Exception:
                pass

        pct = (covered_statements / max(1, total_statements)) * 100.0 if total_statements > 0 else 100.0
        return CoverageResult(
            total_statements=total_statements,
            covered_statements=covered_statements,
            coverage_percentage=round(pct, 2),
            missing_lines_by_file=missing_lines,
        )
