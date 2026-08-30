"""Dependency graph builder.

Scans Python files, builds an import dependency graph, and detects
circular dependencies.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


@dataclass
class DependencyGraph:
    """Directed graph of module dependencies."""

    nodes: List[str] = field(default_factory=list)
    edges: List[Tuple[str, str]] = field(default_factory=list)
    adjacency: Dict[str, List[str]] = field(default_factory=dict)
    cycles: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes),
            "edges": [{"from": f, "to": t} for f, t in self.edges],
            "adjacency": {k: list(v) for k, v in self.adjacency.items()},
            "cycles": list(self.cycles),
        }


class DependencyGraphBuilder:
    """Build dependency graphs from Python source files."""

    def __init__(self, project_path: str = "."):
        self.project_path = os.path.abspath(project_path)
        self.ignored_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}

    def build(self) -> DependencyGraph:
        """Build dependency graph from project."""
        graph = DependencyGraph()
        module_map = self._map_modules()
        imports = self._extract_imports(module_map)

        # Build nodes and edges
        graph.nodes = sorted(module_map.keys())
        for src, targets in imports.items():
            for target in targets:
                if target in module_map:
                    graph.edges.append((src, target))
                    graph.adjacency.setdefault(src, []).append(target)

        # Detect cycles
        graph.cycles = self._detect_cycles(graph.adjacency)
        return graph

    def _map_modules(self) -> Dict[str, str]:
        """Map module keys to file paths."""
        module_map = {}
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, self.project_path)
                rel_path = rel_path.replace(os.sep, "/")
                # Multiple keys for lookup
                module_map[rel_path] = filepath
                module_name = rel_path.replace("/", ".").replace(".py", "")
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]
                module_map[module_name] = filepath
                stem = os.path.splitext(rel_path)[0].replace("/", ".")
                module_map[stem] = filepath
        return module_map

    def _extract_imports(self, module_map: Dict[str, str]) -> Dict[str, Set[str]]:
        """Extract imports from all Python files."""
        imports: Dict[str, Set[str]] = {}
        for rel_path in list(module_map.keys()):
            if not rel_path.endswith(".py"):
                continue
            filepath = module_map[rel_path]
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                tree = ast.parse(content, filename=rel_path)
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue

            file_imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        file_imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        file_imports.add(node.module.split(".")[0])
                    for alias in node.names:
                        file_imports.add(alias.name.split(".")[0])

            # Normalize to module keys
            normalized = set()
            for imp in file_imports:
                for key in module_map:
                    if key.replace("/", ".").replace(".py", "").startswith(imp) or key.startswith(imp):
                        normalized.add(key)
                        break

            imports[rel_path] = normalized
        return imports

    def _detect_cycles(self, adjacency: Dict[str, List[str]]) -> List[List[str]]:
        """Detect cycles using DFS."""
        cycles = []
        visited: Dict[str, int] = {}
        path: List[str] = []

        def dfs(node: str):
            visited[node] = 1
            path.append(node)
            for neighbor in adjacency.get(node, []):
                if neighbor == node:
                    continue
                if visited.get(neighbor, 0) == 1:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor)
            path.pop()
            visited[node] = 2

        for node in adjacency:
            if visited.get(node, 0) == 0:
                dfs(node)

        return cycles
