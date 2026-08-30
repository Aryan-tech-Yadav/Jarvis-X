"""Autonomous Performance Profiler and Optimization Engine."""

from __future__ import annotations

import ast
import os
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .models.quality_result import PerformanceResult


class PerformanceEngine:
    """Profiles runtime, memory allocations, queries, and detects algorithmic bottlenecks."""

    def __init__(self, root_path: Optional[str] = None):
        self.root_path = Path(root_path).resolve() if root_path else Path.cwd()
        self.ignored_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}

    def profile_callable(
        self, target_callable: Callable, *args, **kwargs
    ) -> Tuple[Any, PerformanceResult]:
        tracemalloc.start()
        start_time = time.perf_counter()

        result = None
        error = None
        try:
            result = target_callable(*args, **kwargs)
        except Exception as e:
            error = e
        finally:
            elapsed = time.perf_counter() - start_time
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        if error is not None:
            raise error

        perf_score = 100.0
        bottlenecks: List[Dict[str, Any]] = []
        suggestions: List[str] = []

        if elapsed > 1.0:
            perf_score -= min(40.0, (elapsed - 1.0) * 15.0)
            bottlenecks.append({
                "type": "slow_execution",
                "observed": f"{elapsed:.3f}s",
                "threshold": "1.0s",
                "message": f"Execution took {elapsed:.3f}s, exceeding 1.0s target.",
            })
            suggestions.append("Optimize CPU-bound tasks with memoization, multiprocessing, or vectorized operations.")

        if peak_mem > 50 * 1024 * 1024:  # 50MB
            mb = peak_mem / (1024 * 1024)
            perf_score -= min(30.0, (mb - 50.0) * 0.5)
            bottlenecks.append({
                "type": "high_memory_usage",
                "observed": f"{mb:.1f}MB",
                "threshold": "50MB",
                "message": f"Peak memory allocation was {mb:.1f}MB.",
            })
            suggestions.append("Use generators or stream processing to reduce memory footprint.")

        perf_res = PerformanceResult(
            performance_score=round(max(10.0, perf_score), 2),
            runtime_seconds=elapsed,
            memory_bytes=peak_mem,
            api_latency_ms=elapsed * 1000.0,
            bottlenecks=bottlenecks,
            suggestions=suggestions,
        )

        return result, perf_res

    def analyze_static_performance(self, target_dir: Optional[str] = None) -> PerformanceResult:
        dir_path = Path(target_dir).resolve() if target_dir else self.root_path
        py_files = self._collect_python_files(dir_path)

        bottlenecks: List[Dict[str, Any]] = []
        suggestions: List[str] = []
        db_queries = 0
        duplicate_queries = 0

        for file_path in py_files:
            rel_path = str(file_path.relative_to(dir_path)).replace("\\", "/")
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=rel_path)
            except Exception:
                continue

            file_bottlenecks, n1_count = self._inspect_ast_performance(rel_path, tree)
            bottlenecks.extend(file_bottlenecks)
            db_queries += n1_count

        # Compute static score
        penalty = len(bottlenecks) * 8.0 + (db_queries * 12.0)
        perf_score = max(20.0, 100.0 - penalty)

        if any(b.get("type") == "nested_loop_complexity" for b in bottlenecks):
            suggestions.append("Refactor nested loops O(N^2) into hash maps / dictionary lookups O(1).")
        if any(b.get("type") == "n_plus_one_query" for b in bottlenecks):
            suggestions.append("Eliminate N+1 database queries by batch fetching with 'IN' clauses or eager JOINs.")
        if any(b.get("type") == "linear_membership_test" for b in bottlenecks):
            suggestions.append("Convert lists to sets before membership testing ('in' operator) inside loops.")

        if not suggestions:
            suggestions.append("Code passes performance efficiency checks.")

        return PerformanceResult(
            performance_score=round(perf_score, 2),
            runtime_seconds=0.0,
            db_query_count=db_queries,
            duplicate_queries=duplicate_queries,
            bottlenecks=bottlenecks,
            suggestions=suggestions,
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


    def _inspect_ast_performance(self, rel_path: str, tree: ast.AST) -> Tuple[List[Dict[str, Any]], int]:
        bottlenecks: List[Dict[str, Any]] = []
        n1_queries = 0

        for node in ast.walk(tree):
            # 1. Nested Loop Detection (O(N^2) or O(N^3))
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.For, ast.While)):
                        bottlenecks.append({
                            "file": rel_path,
                            "line": node.lineno,
                            "type": "nested_loop_complexity",
                            "severity": "medium",
                            "message": f"Nested loop at line {node.lineno} may cause O(N^2) time complexity bottleneck.",
                        })

                # 2. Database Query Inside Loop (N+1 Query Pattern)
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Call):
                        call_name = ""
                        if isinstance(inner.func, ast.Attribute):
                            call_name = inner.func.attr
                        elif isinstance(inner.func, ast.Name):
                            call_name = inner.func.id

                        if call_name in {"execute", "raw", "select", "query", "filter", "get"}:
                            # Check if caller looks like db / session / cursor / model
                            caller_str = ast.unparse(inner.func.value).lower() if (hasattr(ast, "unparse") and hasattr(inner.func, "value")) else ""
                            if any(k in caller_str for k in ["db", "session", "cursor", "repo", "model", "query", "objects"]):
                                n1_queries += 1
                                bottlenecks.append({
                                    "file": rel_path,
                                    "line": inner.lineno,
                                    "type": "n_plus_one_query",
                                    "severity": "high",
                                    "message": f"Database query '{call_name}()' executed inside loop at line {inner.lineno} (N+1 query anti-pattern).",
                                })

            # 3. Repeated file read / open in loop
            if isinstance(node, (ast.For, ast.While)):
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == "open":
                        bottlenecks.append({
                            "file": rel_path,
                            "line": inner.lineno,
                            "type": "repeated_io_in_loop",
                            "severity": "medium",
                            "message": f"File I/O 'open()' inside loop at line {inner.lineno}. Read/buffer once outside loop.",
                        })

        return bottlenecks, n1_queries
