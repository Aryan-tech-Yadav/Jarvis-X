"""Dependency scanner for Python projects.

Builds import dependency graphs and detects:
  - circular dependencies
  - unused imports
  - heavy modules (high fan-in)
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DependencyError(Exception):
    """Base dependency error."""


@dataclass
class ImportEdge:
    """Single import dependency edge."""

    source: str
    target: str
    lineno: int = 0
    names: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "lineno": self.lineno,
            "names": list(self.names),
        }


@dataclass
class DependencyGraph:
    """Complete dependency graph for a project."""

    nodes: List[str] = field(default_factory=list)
    edges: List[ImportEdge] = field(default_factory=list)
    adjacency: Dict[str, List[str]] = field(default_factory=dict)
    reverse_adjacency: Dict[str, List[str]] = field(default_factory=dict)
    cycles: List[List[str]] = field(default_factory=list)
    unused_imports: List[ImportEdge] = field(default_factory=list)
    heavy_modules: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": list(self.nodes),
            "edges": [e.to_dict() for e in self.edges],
            "adjacency": {k: list(v) for k, v in self.adjacency.items()},
            "reverse_adjacency": {k: list(v) for k, v in self.reverse_adjacency.items()},
            "cycles": list(self.cycles),
            "unused_imports": [e.to_dict() for e in self.unused_imports],
            "heavy_modules": list(self.heavy_modules),
        }


class DependencyScanner:
    """Build and analyze Python dependency graphs."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self._module_map: Dict[str, str] = {}

    def scan(self, files: Dict[str, str]) -> DependencyGraph:
        """Build dependency graph from parsed files.

        Args:
            files: Mapping of relative path to file content.

        Returns:
            DependencyGraph with all dependencies.
        """
        graph = DependencyGraph()
        self._build_module_map(files)
        graph.nodes = sorted(self._module_map.keys())

        # Extract imports
        for rel_path, content in files.items():
            self._extract_imports(rel_path, content, graph)

        # Build adjacency lists using module names
        module_name_map = {v: k for k, v in self._module_map.items()}
        for edge in graph.edges:
            source_module = module_name_map.get(edge.source, edge.source)
            graph.adjacency.setdefault(source_module, []).append(edge.target)
            graph.reverse_adjacency.setdefault(edge.target, []).append(source_module)

        # Detect cycles
        graph.cycles = self._detect_cycles(graph.adjacency)

        # Detect unused imports
        graph.unused_imports = self._find_unused_imports(files, graph)

        # Detect heavy modules
        graph.heavy_modules = self._find_heavy_modules(graph)

        return graph

    def _build_module_map(self, files: Dict[str, str]):
        """Build mapping of module names to file paths."""
        self._module_map.clear()
        for rel_path in files:
            normalized = rel_path.replace("/", ".").replace(".py", "")
            if normalized.endswith(".__init__"):
                normalized = normalized[:-9]
            self._module_map[normalized] = rel_path
            stem = rel_path.replace("/", ".").replace(".py", "")
            self._module_map[stem] = rel_path

    def _extract_imports(self, rel_path: str, content: str, graph: DependencyGraph):
        """Extract imports from a file and add to graph."""
        try:
            tree = ast.parse(content, filename=rel_path)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name.split(".")[0]
                    if self._is_internal_module(target):
                        graph.edges.append(ImportEdge(
                            source=rel_path,
                            target=target,
                            lineno=node.lineno,
                            names=[alias.name],
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    target = node.module.split(".")[0]
                    if self._is_internal_module(target):
                        names = [alias.name for alias in node.names]
                        graph.edges.append(ImportEdge(
                            source=rel_path,
                            target=target,
                            lineno=node.lineno,
                            names=names,
                        ))

    def _is_internal_module(self, name: str) -> bool:
        """Check if module is internal to the project."""
        if not name:
            return False
        # Check if it matches any known internal module
        for module_key in self._module_map:
            parts = module_key.split(".")
            if parts and parts[0] == name:
                return True
        return False

    def _detect_cycles(self, adjacency: Dict[str, List[str]]) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        cycles: List[List[str]] = []
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

    def _find_unused_imports(self, files: Dict[str, str], graph: DependencyGraph) -> List[ImportEdge]:
        """Find imports that are never used."""
        unused = []
        for edge in graph.edges:
            # Check if any imported name is actually used in the file
            content = files.get(edge.source, "")
            used_names = set()
            for line in content.splitlines():
                for name in edge.names:
                    if name in line:
                        used_names.add(name)
            if not used_names:
                unused.append(edge)
        return unused

    def _find_heavy_modules(self, graph: DependencyGraph) -> List[Dict[str, Any]]:
        """Find modules with many incoming dependencies (fan-in > 10)."""
        fan_in: Dict[str, int] = {}
        for edge in graph.edges:
            fan_in[edge.target] = fan_in.get(edge.target, 0) + 1

        heavy = []
        for module, count in sorted(fan_in.items(), key=lambda x: x[1], reverse=True):
            if count > 10:
                heavy.append({
                    "module": module,
                    "fan_in": count,
                    "risk": "high" if count > 20 else "medium",
                })
        return heavy[:20]  # Top 20 heavy modules
