"""Autonomous QA Engine & Static Code Analyzer."""

from __future__ import annotations

import ast
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models.quality_result import (
    CategoryScore,
    IssueSeverity,
    QualityCategory,
    QualityIssue,
    QualityScore,
    StaticAnalysisResult,
)


class StaticAnalyzer:
    """AST-based static analyzer for code complexity, dead code, duplicates, and smells."""

    MAX_FUNCTION_LINES = 60
    MAX_FUNCTION_ARGS = 6
    MAX_CLASS_LINES = 400
    MAX_CLASS_METHODS = 18
    HIGH_COMPLEXITY_THRESHOLD = 10
    MEDIUM_COMPLEXITY_THRESHOLD = 5

    def __init__(self, root_path: Optional[str] = None):
        self.root_path = Path(root_path).resolve() if root_path else Path.cwd()
        self.ignored_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", "dist", "build"}

    def scan_directory(self, target_dir: Optional[str] = None) -> StaticAnalysisResult:
        dir_path = Path(target_dir).resolve() if target_dir else self.root_path
        py_files = self._collect_python_files(dir_path)

        issues: List[QualityIssue] = []
        dead_files: List[str] = []
        dead_functions: List[Dict[str, Any]] = []
        duplicate_blocks: List[Dict[str, Any]] = []
        circular_imports: List[List[str]] = []
        large_functions: List[Dict[str, Any]] = []
        large_classes: List[Dict[str, Any]] = []
        unused_variables: List[Dict[str, Any]] = []
        architecture_violations: List[Dict[str, Any]] = []

        # Parse ASTs
        parsed_trees: Dict[str, Tuple[ast.AST, str]] = {}
        for file_path in py_files:
            rel_path = str(file_path.relative_to(dir_path)).replace("\\", "/")
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=rel_path)
                parsed_trees[rel_path] = (tree, content)
            except SyntaxError as e:
                issues.append(
                    QualityIssue(
                        file=rel_path,
                        line=e.lineno or 1,
                        rule="syntax_error",
                        message=f"Syntax error: {e.msg}",
                        severity=IssueSeverity.CRITICAL,
                        category=QualityCategory.CODE_QUALITY,
                        suggestion="Fix invalid Python syntax",
                    )
                )

        # 1. Complexity & Code Smells
        complexity_scores: List[int] = []
        for rel_path, (tree, content) in parsed_trees.items():
            file_issues, file_lf, file_lc, file_uv, f_complexities = self._analyze_file_ast(rel_path, tree, content)
            issues.extend(file_issues)
            large_functions.extend(file_lf)
            large_classes.extend(file_lc)
            unused_variables.extend(file_uv)
            complexity_scores.extend(f_complexities)

        # 2. Dead Code & Uncalled Functions
        dead_funcs, dead_fls = self._detect_dead_code(parsed_trees, dir_path)
        dead_functions.extend(dead_funcs)
        dead_files.extend(dead_fls)
        for df in dead_funcs:
            issues.append(
                QualityIssue(
                    file=df["file"],
                    line=df["line"],
                    rule="dead_function",
                    message=f"Function or method '{df['name']}' is defined but never called or referenced.",
                    severity=IssueSeverity.LOW,
                    category=QualityCategory.CODE_QUALITY,
                    suggestion=f"Remove or expose uncalled function '{df['name']}'",
                )
            )

        # 3. Duplicate Code Detection
        duplicate_blocks = self._detect_duplicates(parsed_trees)
        for dup in duplicate_blocks:
            issues.append(
                QualityIssue(
                    file=dup["file_a"],
                    line=dup["line_a"],
                    rule="duplicate_logic",
                    message=f"Duplicate logic block ({dup['lines_count']} lines) found in '{dup['file_b']}' at line {dup['line_b']}.",
                    severity=IssueSeverity.MEDIUM,
                    category=QualityCategory.CODE_QUALITY,
                    suggestion="Extract duplicate logic into a shared helper function",
                )
            )

        # 4. Circular Import Detection
        circular_imports = self._detect_circular_imports(parsed_trees)
        for cycle in circular_imports:
            cycle_str = " -> ".join(cycle)
            issues.append(
                QualityIssue(
                    file=cycle[0],
                    line=1,
                    rule="circular_import",
                    message=f"Circular import cycle detected: {cycle_str}",
                    severity=IssueSeverity.HIGH,
                    category=QualityCategory.ARCHITECTURE,
                    suggestion="Move shared interfaces to a separate core module or refactor imports",
                )
            )

        # Calculate average complexity
        avg_complexity = sum(complexity_scores) / max(1, len(complexity_scores)) if complexity_scores else 1.0
        if avg_complexity > self.HIGH_COMPLEXITY_THRESHOLD:
            complexity_level = "High"
            complexity_score = max(30.0, 100.0 - (avg_complexity - self.HIGH_COMPLEXITY_THRESHOLD) * 6.0)
        elif avg_complexity > self.MEDIUM_COMPLEXITY_THRESHOLD:
            complexity_level = "Medium"
            complexity_score = max(70.0, 100.0 - (avg_complexity - self.MEDIUM_COMPLEXITY_THRESHOLD) * 5.0)
        else:
            complexity_level = "Low"
            complexity_score = 100.0

        return StaticAnalysisResult(
            complexity_score=round(complexity_score, 2),
            complexity_level=complexity_level,
            dead_files=dead_files,
            dead_functions=dead_functions,
            duplicate_blocks=duplicate_blocks,
            circular_imports=circular_imports,
            large_functions=large_functions,
            large_classes=large_classes,
            unused_variables=unused_variables,
            architecture_violations=architecture_violations,
            issues=issues,
        )


    def _collect_python_files(self, dir_path: Path) -> List[Path]:
        if dir_path.is_file() and dir_path.suffix == ".py":
            return [dir_path]
        py_files: List[Path] = []
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            for file in files:
                if file.endswith(".py"):
                    py_files.append(Path(root) / file)
        return py_files

    def _analyze_file_ast(
        self, rel_path: str, tree: ast.AST, content: str
    ) -> Tuple[List[QualityIssue], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[int]]:
        issues: List[QualityIssue] = []
        large_functions: List[Dict[str, Any]] = []
        large_classes: List[Dict[str, Any]] = []
        unused_variables: List[Dict[str, Any]] = []
        complexities: List[int] = []

        lines = content.splitlines()

        for node in ast.walk(tree):
            # Check function size, args, complexity
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, "end_lineno", node.lineno)
                line_count = end_line - node.lineno + 1
                arg_count = len(node.args.args)
                complexity = self._compute_cyclomatic_complexity(node)
                complexities.append(complexity)

                if line_count > self.MAX_FUNCTION_LINES:
                    lf = {"file": rel_path, "name": node.name, "line": node.lineno, "lines": line_count}
                    large_functions.append(lf)
                    issues.append(
                        QualityIssue(
                            file=rel_path,
                            line=node.lineno,
                            rule="large_function",
                            message=f"Function '{node.name}' is too long ({line_count} lines > {self.MAX_FUNCTION_LINES}).",
                            severity=IssueSeverity.MEDIUM,
                            category=QualityCategory.CODE_QUALITY,
                            suggestion=f"Refactor '{node.name}' into smaller sub-functions",
                        )
                    )

                if arg_count > self.MAX_FUNCTION_ARGS:
                    issues.append(
                        QualityIssue(
                            file=rel_path,
                            line=node.lineno,
                            rule="too_many_arguments",
                            message=f"Function '{node.name}' takes {arg_count} arguments (max recommended is {self.MAX_FUNCTION_ARGS}).",
                            severity=IssueSeverity.LOW,
                            category=QualityCategory.CODE_QUALITY,
                            suggestion="Group arguments into a config object or dataclass",
                        )
                    )

                if complexity > self.HIGH_COMPLEXITY_THRESHOLD:
                    issues.append(
                        QualityIssue(
                            file=rel_path,
                            line=node.lineno,
                            rule="high_complexity",
                            message=f"Function '{node.name}' has high cyclomatic complexity ({complexity} > {self.HIGH_COMPLEXITY_THRESHOLD}).",
                            severity=IssueSeverity.HIGH,
                            category=QualityCategory.CODE_QUALITY,
                            suggestion=f"Simplify conditional branches in '{node.name}'",
                        )
                    )

                # Check unused variables in function
                uv_list = self._find_unused_variables(node, rel_path)
                unused_variables.extend(uv_list)
                for uv in uv_list:
                    issues.append(
                        QualityIssue(
                            file=rel_path,
                            line=uv["line"],
                            rule="unused_variable",
                            message=f"Local variable '{uv['name']}' is assigned but never used.",
                            severity=IssueSeverity.LOW,
                            category=QualityCategory.CODE_QUALITY,
                            suggestion=f"Remove or prefix with '_' for intentional unused variable '{uv['name']}'",
                        )
                    )

                # Check mutable default args
                for default_node in node.args.defaults + [d for d in node.args.kw_defaults if d]:
                    if isinstance(default_node, (ast.List, ast.Dict, ast.Set)):
                        issues.append(
                            QualityIssue(
                                file=rel_path,
                                line=default_node.lineno,
                                rule="mutable_default_argument",
                                message=f"Mutable default argument used in function '{node.name}'.",
                                severity=IssueSeverity.HIGH,
                                category=QualityCategory.CODE_QUALITY,
                                suggestion="Use None as default and initialize inside function body",
                            )
                        )

            # Check class size and method count
            elif isinstance(node, ast.ClassDef):
                end_line = getattr(node, "end_lineno", node.lineno)
                line_count = end_line - node.lineno + 1
                methods = [m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                method_count = len(methods)

                if line_count > self.MAX_CLASS_LINES or method_count > self.MAX_CLASS_METHODS:
                    lc = {"file": rel_path, "name": node.name, "line": node.lineno, "lines": line_count, "methods": method_count}
                    large_classes.append(lc)
                    issues.append(
                        QualityIssue(
                            file=rel_path,
                            line=node.lineno,
                            rule="large_class",
                            message=f"Class '{node.name}' is too large ({line_count} lines, {method_count} methods).",
                            severity=IssueSeverity.MEDIUM,
                            category=QualityCategory.ARCHITECTURE,
                            suggestion=f"Split '{node.name}' into smaller focused service classes",
                        )
                    )

            # Check bare except
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(
                        QualityIssue(
                            file=rel_path,
                            line=node.lineno,
                            rule="bare_except",
                            message="Bare 'except:' catches all exceptions including system exits.",
                            severity=IssueSeverity.HIGH,
                            category=QualityCategory.CODE_QUALITY,
                            suggestion="Specify exception types or catch 'Exception'",
                        )
                    )

            # Check wildcard import
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        issues.append(
                            QualityIssue(
                                file=rel_path,
                                line=node.lineno,
                                rule="wildcard_import",
                                message=f"Wildcard import 'from {node.module} import *' pollutes namespace.",
                                severity=IssueSeverity.MEDIUM,
                                category=QualityCategory.CODE_QUALITY,
                                suggestion="Import explicit symbols instead of wildcard",
                            )
                        )

        return issues, large_functions, large_classes, unused_variables, complexities


    def _compute_cyclomatic_complexity(self, func_node: ast.AST) -> int:
        complexity = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                complexity += len(node.generators)
            elif isinstance(node, ast.IfExp):
                complexity += 1
            elif isinstance(node, ast.Assert):
                complexity += 1
        return complexity

    def _find_unused_variables(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str) -> List[Dict[str, Any]]:
        assigned_vars: Dict[str, int] = {}
        used_vars: Set[str] = set()

        for node in ast.walk(func_node):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    if not node.id.startswith("_") and node.id not in {"self", "cls"}:
                        assigned_vars[node.id] = node.lineno
                elif isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)

        unused = []
        for var_name, lineno in assigned_vars.items():
            if var_name not in used_vars:
                unused.append({"file": file_path, "name": var_name, "line": lineno})
        return unused

    def _detect_dead_code(
        self, parsed_trees: Dict[str, Tuple[ast.AST, str]], root_dir: Path
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        defined_functions: Dict[str, Tuple[str, int]] = {}
        called_names: Set[str] = set()
        imported_modules: Set[str] = set()

        for rel_path, (tree, _) in parsed_trees.items():
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Ignore special dunder methods and test functions
                    if not node.name.startswith("__") and not node.name.startswith("test_"):
                        defined_functions[node.name] = (rel_path, node.lineno)
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        called_names.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        called_names.add(node.func.attr)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_modules.add(node.module.split(".")[0])
                    for alias in node.names:
                        called_names.add(alias.name)

        dead_functions = []
        for name, (fpath, lno) in defined_functions.items():
            if name.startswith("_") and not name.startswith("__"):
                # Private methods/functions not called anywhere
                if name not in called_names:
                    dead_functions.append({"file": fpath, "name": name, "line": lno})

        # Dead files: files not imported and not entry points / tests
        dead_files = []
        entry_points = {"main.py", "app.py", "cli.py", "__init__.py", "setup.py", "manage.py"}
        for rel_path in parsed_trees.keys():
            base_name = Path(rel_path).name
            mod_name = Path(rel_path).stem
            if base_name in entry_points or "test" in rel_path.lower() or base_name.startswith("__"):
                continue
            if mod_name not in imported_modules and mod_name not in called_names:
                # Check if imported anywhere by relative or absolute name
                imported = any(mod_name in text for _, (_, text) in parsed_trees.items() if _ != rel_path)
                if not imported:
                    dead_files.append(rel_path)

        return dead_functions, dead_files

    def _detect_duplicates(self, parsed_trees: Dict[str, Tuple[ast.AST, str]]) -> List[Dict[str, Any]]:
        blocks: Dict[str, List[Tuple[str, int, int]]] = defaultdict(list)
        min_block_lines = 4

        for rel_path, (_, content) in parsed_trees.items():
            lines = [line.strip() for line in content.splitlines()]
            for i in range(len(lines) - min_block_lines + 1):
                block_chunk = [lines[j] for j in range(i, i + min_block_lines) if lines[j] and not lines[j].startswith("#")]
                if len(block_chunk) >= min_block_lines:
                    block_key = "\n".join(block_chunk)
                    blocks[block_key].append((rel_path, i + 1, min_block_lines))

        duplicates = []
        seen_pairs: Set[Tuple[str, int, str, int]] = set()
        for block_key, occurrences in blocks.items():
            if len(occurrences) > 1:
                first = occurrences[0]
                for other in occurrences[1:]:
                    pair_key = (first[0], first[1], other[0], other[1])
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        duplicates.append({
                            "file_a": first[0],
                            "line_a": first[1],
                            "file_b": other[0],
                            "line_b": other[1],
                            "lines_count": first[2],
                        })
        return duplicates[:15]  # Limit top duplicates

    def _detect_circular_imports(self, parsed_trees: Dict[str, Tuple[ast.AST, str]]) -> List[List[str]]:
        graph: Dict[str, Set[str]] = defaultdict(set)
        mod_map: Dict[str, str] = {}

        for rel_path in parsed_trees.keys():
            mod_key = rel_path.replace("/", ".").replace(".py", "")
            if mod_key.endswith(".__init__"):
                mod_key = mod_key[:-9]
            mod_map[mod_key] = rel_path
            stem = Path(rel_path).stem
            mod_map[stem] = rel_path

        for rel_path, (tree, _) in parsed_trees.items():
            src_key = rel_path.replace("/", ".").replace(".py", "")
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = alias.name
                        if target in mod_map:
                            graph[rel_path].add(mod_map[target])
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module in mod_map:
                        graph[rel_path].add(mod_map[node.module])

        # Cycle finding via DFS
        cycles: List[List[str]] = []
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        path: List[str] = []

        def dfs(node: str):
            visited[node] = 1
            path.append(node)
            for neighbor in graph.get(node, set()):
                if neighbor == node:
                    continue
                if visited.get(neighbor, 0) == 1:
                    cycle_idx = path.index(neighbor)
                    cycle = path[cycle_idx:] + [neighbor]
                    if len(cycle) > 2 and cycle not in cycles:
                        cycles.append(cycle)
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor)
            path.pop()
            visited[node] = 2

        for node in list(graph.keys()):
            if visited.get(node, 0) == 0:
                dfs(node)

        return cycles



class QAEngine:
    """Enterprise QA Engine evaluating coding standards, architecture, naming, and docs."""

    SNAKE_CASE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
    PASCAL_CASE_PATTERN = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
    UPPER_CASE_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")

    FORBIDDEN_LAYER_IMPORTS = {
        # Domain / Models should not import UI or Controller
        "models": ["controllers", "views", "api", "ui", "routes"],
        "core": ["plugins", "ui", "api_client", "cli"],
        "entities": ["infrastructure", "database", "api"],
    }

    def __init__(self, root_path: Optional[str] = None):
        self.root_path = Path(root_path).resolve() if root_path else Path.cwd()
        self.static_analyzer = StaticAnalyzer(self.root_path)

    def evaluate_quality(self, target_dir: Optional[str] = None, is_snippet: bool = False) -> Tuple[QualityScore, StaticAnalysisResult]:
        dir_path = Path(target_dir).resolve() if target_dir else self.root_path

        static_result = self.static_analyzer.scan_directory(str(dir_path))

        # Category Issues Collection
        arch_issues = self.check_architecture_rules(str(dir_path)) + [i for i in static_result.issues if i.category == QualityCategory.ARCHITECTURE]
        code_issues = self.check_coding_standards(str(dir_path)) + self.check_naming_rules(str(dir_path)) + [i for i in static_result.issues if i.category == QualityCategory.CODE_QUALITY]
        doc_issues, doc_metrics = self.check_documentation(str(dir_path))
        struct_issues = [] if is_snippet else self.check_project_structure(str(dir_path))
        config_issues = [] if is_snippet else self.check_configurations(str(dir_path))

        all_issues = arch_issues + code_issues + doc_issues + struct_issues + config_issues

        # Category Scores Calculation (0-100)
        arch_score = max(0.0, 100.0 - (len([i for i in arch_issues if i.severity == IssueSeverity.CRITICAL]) * 25.0 + len([i for i in arch_issues if i.severity == IssueSeverity.HIGH]) * 10.0 + len([i for i in arch_issues if i.severity == IssueSeverity.MEDIUM]) * 4.0))
        code_score = max(0.0, min(100.0, static_result.complexity_score - (len([i for i in code_issues if i.severity == IssueSeverity.CRITICAL]) * 20.0 + len([i for i in code_issues if i.severity == IssueSeverity.HIGH]) * 8.0 + len([i for i in code_issues if i.severity == IssueSeverity.MEDIUM]) * 2.0 + len([i for i in code_issues if i.severity == IssueSeverity.LOW]) * 0.5)))
        doc_score = max(0.0, min(100.0, float(doc_metrics.get("docstring_coverage", 85.0)) - (len(doc_issues) * 3.0)))

        struct_penalty = len([i for i in struct_issues + config_issues if i.severity in (IssueSeverity.CRITICAL, IssueSeverity.HIGH)]) * 15.0 + len([i for i in struct_issues + config_issues if i.severity == IssueSeverity.MEDIUM]) * 5.0
        arch_score = max(0.0, arch_score - struct_penalty * 0.3)

        category_scores: Dict[str, CategoryScore] = {
            "architecture": CategoryScore(category=QualityCategory.ARCHITECTURE, score=arch_score, weight=0.35, issues=arch_issues),
            "code_quality": CategoryScore(category=QualityCategory.CODE_QUALITY, score=code_score, weight=0.45, issues=code_issues),
            "documentation": CategoryScore(category=QualityCategory.DOCUMENTATION, score=doc_score, weight=0.20, issues=doc_issues, metrics=doc_metrics),
        }

        # Overall weighted score
        overall_score = sum(cs.score * cs.weight for cs in category_scores.values())

        # Grade calculation
        if overall_score >= 95.0:
            grade = "A+"
        elif overall_score >= 90.0:
            grade = "A"
        elif overall_score >= 80.0:
            grade = "B"
        elif overall_score >= 70.0:
            grade = "C"
        elif overall_score >= 60.0:
            grade = "D"
        else:
            grade = "F"

        critical_count = len([i for i in all_issues if i.severity == IssueSeverity.CRITICAL])
        high_count = len([i for i in all_issues if i.severity == IssueSeverity.HIGH])
        warnings_count = len([i for i in all_issues if i.severity in (IssueSeverity.MEDIUM, IssueSeverity.LOW, IssueSeverity.INFO)])

        gate_reasons = []
        passed_gate = True
        if critical_count > 0:
            passed_gate = False
            gate_reasons.append(f"Contains {critical_count} critical issues")
        if overall_score < 90.0:
            passed_gate = False
            gate_reasons.append(f"Overall quality score ({overall_score:.1f}) is below release threshold (90.0)")

        # Generate Actionable Suggestions
        suggestions: List[str] = []
        if static_result.circular_imports:
            suggestions.append("Resolve circular imports by extracting shared interfaces into a core module.")
        if len(static_result.large_classes) > 0:
            for lc in static_result.large_classes[:3]:
                suggestions.append(f"Split large class '{lc['name']}' in {lc['file']} into smaller specialized services.")
        if len(static_result.large_functions) > 0:
            for lf in static_result.large_functions[:3]:
                suggestions.append(f"Refactor long function '{lf['name']}' in {lf['file']} ({lf['lines']} lines) into subroutines.")
        if static_result.duplicate_blocks:
            suggestions.append(f"Extract {len(static_result.duplicate_blocks)} duplicated logic blocks into shared utility functions.")
        if doc_score < 80.0:
            suggestions.append("Increase docstring coverage on public classes and API methods.")

        if not suggestions and passed_gate:
            suggestions.append("Code meets senior engineering QA standards.")

        quality_score = QualityScore(
            overall_score=round(overall_score, 2),
            category_scores=category_scores,
            grade=grade,
            passed_gate=passed_gate,
            gate_reasons=gate_reasons,
            critical_issues_count=critical_count,
            warnings_count=warnings_count + high_count,
            suggestions=suggestions,
        )

        return quality_score, static_result

    def check_coding_standards(self, target_dir: str) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        py_files = self.static_analyzer._collect_python_files(Path(target_dir))
        for p in py_files:
            rel = str(p.relative_to(target_dir)).replace("\\", "/")
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                if len(lines) > 800:
                    issues.append(
                        QualityIssue(
                            file=rel,
                            line=len(lines),
                            rule="file_too_long",
                            message=f"File exceeds 800 lines ({len(lines)} lines).",
                            severity=IssueSeverity.LOW,
                            category=QualityCategory.CODE_QUALITY,
                            suggestion="Decompose file into multiple cohesive modules",
                        )
                    )
            except Exception:
                pass
        return issues

    def check_naming_rules(self, target_dir: str) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        py_files = self.static_analyzer._collect_python_files(Path(target_dir))
        for p in py_files:
            rel = str(p.relative_to(target_dir)).replace("\\", "/")
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=rel)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if not self.PASCAL_CASE_PATTERN.match(node.name):
                            issues.append(
                                QualityIssue(
                                    file=rel,
                                    line=node.lineno,
                                    rule="naming_class_pascal_case",
                                    message=f"Class name '{node.name}' should follow PascalCase convention.",
                                    severity=IssueSeverity.LOW,
                                    category=QualityCategory.CODE_QUALITY,
                                    suggestion=f"Rename '{node.name}' to PascalCase",
                                )
                            )
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not node.name.startswith("__") and not self.SNAKE_CASE_PATTERN.match(node.name):
                            issues.append(
                                QualityIssue(
                                    file=rel,
                                    line=node.lineno,
                                    rule="naming_function_snake_case",
                                    message=f"Function name '{node.name}' should follow snake_case convention.",
                                    severity=IssueSeverity.LOW,
                                    category=QualityCategory.CODE_QUALITY,
                                    suggestion=f"Rename '{node.name}' to snake_case",
                                )
                            )
            except Exception:
                pass
        return issues

    def check_architecture_rules(self, target_dir: str) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        py_files = self.static_analyzer._collect_python_files(Path(target_dir))
        for p in py_files:
            rel = str(p.relative_to(target_dir)).replace("\\", "/")
            parts = rel.lower().split("/")
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=rel)
                for layer, forbidden_targets in self.FORBIDDEN_LAYER_IMPORTS.items():
                    if layer in parts:
                        for node in ast.walk(tree):
                            imported = []
                            if isinstance(node, ast.Import):
                                imported.extend(a.name for a in node.names)
                            elif isinstance(node, ast.ImportFrom) and node.module:
                                imported.append(node.module)

                            for imp in imported:
                                for forbidden in forbidden_targets:
                                    if forbidden in imp.split("."):
                                        issues.append(
                                            QualityIssue(
                                                file=rel,
                                                line=getattr(node, "lineno", 1),
                                                rule="architecture_layer_violation",
                                                message=f"Layer violation: '{layer}' layer must not depend on '{forbidden}' layer ('{imp}').",
                                                severity=IssueSeverity.HIGH,
                                                category=QualityCategory.ARCHITECTURE,
                                                suggestion=f"Invert dependency or use an interface/event bus",
                                            )
                                        )
            except Exception:
                pass
        return issues

    def check_project_structure(self, target_dir: str) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        root = Path(target_dir)
        if not (root / "tests").exists() and not (root / "test").exists():
            issues.append(
                QualityIssue(
                    file="project_root",
                    line=1,
                    rule="missing_tests_directory",
                    message="Project lacks a standard 'tests/' directory.",
                    severity=IssueSeverity.MEDIUM,
                    category=QualityCategory.ARCHITECTURE,
                    suggestion="Create 'tests/' directory with automated unit tests",
                )
            )
        if not (root / "README.md").exists() and not (root / "readme.md").exists():
            issues.append(
                QualityIssue(
                    file="project_root",
                    line=1,
                    rule="missing_readme",
                    message="Project lacks a 'README.md' file.",
                    severity=IssueSeverity.LOW,
                    category=QualityCategory.DOCUMENTATION,
                    suggestion="Add README.md with project overview and instructions",
                )
            )
        return issues

    def check_configurations(self, target_dir: str) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        root = Path(target_dir)
        for conf_file in root.glob("*.json"):
            try:
                import json
                json.loads(conf_file.read_text(encoding="utf-8"))
            except Exception as e:
                issues.append(
                    QualityIssue(
                        file=conf_file.name,
                        line=1,
                        rule="invalid_json_config",
                        message=f"Configuration file '{conf_file.name}' has invalid JSON: {e}",
                        severity=IssueSeverity.CRITICAL,
                        category=QualityCategory.ARCHITECTURE,
                        suggestion="Fix syntax errors in JSON configuration",
                    )
                )
        return issues

    def check_documentation(self, target_dir: str) -> Tuple[List[QualityIssue], Dict[str, Any]]:
        issues: List[QualityIssue] = []
        py_files = self.static_analyzer._collect_python_files(Path(target_dir))
        total_symbols = 0
        documented_symbols = 0

        for p in py_files:
            rel = str(p.relative_to(target_dir)).replace("\\", "/")
            if "test" in rel.lower():
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=rel)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if not node.name.startswith("_"):
                            total_symbols += 1
                            doc = ast.get_docstring(node)
                            if doc:
                                documented_symbols += 1
                            else:
                                issues.append(
                                    QualityIssue(
                                        file=rel,
                                        line=node.lineno,
                                        rule="missing_docstring",
                                        message=f"Public {type(node).__name__.replace('Def', '').lower()} '{node.name}' lacks a docstring.",
                                        severity=IssueSeverity.LOW,
                                        category=QualityCategory.DOCUMENTATION,
                                        suggestion=f"Add docstring describing purpose and parameters of '{node.name}'",
                                    )
                                )
            except Exception:
                pass

        coverage = (documented_symbols / max(1, total_symbols)) * 100.0 if total_symbols > 0 else 100.0
        return issues, {
            "total_public_symbols": total_symbols,
            "documented_symbols": documented_symbols,
            "docstring_coverage": round(coverage, 2),
        }
