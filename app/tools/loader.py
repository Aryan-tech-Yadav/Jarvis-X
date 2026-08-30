"""Dynamic tool loader.

Scans app/tools/ subdirectories and auto-registers tools.
No manual imports required.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Type

from app.tools.base_tool import BaseTool, ToolMetadata


@dataclass
class LoadedTool:
    """A tool loaded from disk."""

    module_path: str
    class_name: str
    tool: BaseTool
    metadata: ToolMetadata

    @property
    def name(self) -> str:
        return self.metadata.name


class ToolLoader:
    """Discover and load tools from the filesystem.

    Scans directories under a root path for Python modules containing
    BaseTool subclasses.
    """

    def __init__(self, tools_root: str = "app/tools"):
        self.tools_root = tools_root
        self._loaded: Dict[str, LoadedTool] = {}
        self._package_prefix = self._compute_prefix(tools_root)

    def _compute_prefix(self, tools_root: str) -> str:
        """Compute the Python package prefix for a tools root directory."""
        root = os.path.abspath(tools_root)
        cwd = os.path.abspath(".")
        try:
            rel = os.path.relpath(root, cwd)
        except ValueError:
            return ""
        if rel == ".":
            return ""
        parts = rel.replace(os.sep, ".").split(".")
        # Remove empty parts
        parts = [p for p in parts if p]
        return ".".join(parts) + "." if parts else ""

    def discover(self) -> List[str]:
        """Return Python module paths for all discovered tool modules."""
        modules: List[str] = []
        if not os.path.isdir(self.tools_root):
            return modules
        root = os.path.abspath(self.tools_root)
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                if filename.startswith("_") or not filename.endswith(".py"):
                    continue
                if filename in {"base_tool.py", "tool_result.py", "tool_metadata.py",
                                "tool_registry.py", "tool_executor.py", "tool_manager.py",
                                "tool_selector.py", "tool_ranker.py", "tool_cache.py",
                                "tool_history.py", "tool_scoring.py", "__init__.py",
                                "loader.py", "permission_manager.py", "tool_chain.py"}:
                    continue
                abs_path = os.path.join(dirpath, filename[:-3])
                try:
                    rel_path = os.path.relpath(abs_path, root)
                except ValueError:
                    continue
                module_name = rel_path.replace(os.sep, ".")
                full_path = f"{self._package_prefix}{module_name}"
                modules.append(full_path)
        return sorted(modules)

    def load(self, module_path: str, class_name: str = "") -> Optional[LoadedTool]:
        """Import a module and instantiate its BaseTool subclass."""
        cache_key = f"{module_path}:{class_name}"
        if cache_key in self._loaded:
            return self._loaded[cache_key]
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            return None
        tool_cls = self._find_tool_class(module, class_name)
        if tool_cls is None:
            return None
        try:
            tool = tool_cls()
        except Exception:
            return None
        loaded = LoadedTool(
            module_path=module_path,
            class_name=tool_cls.__name__,
            tool=tool,
            metadata=tool.metadata,
        )
        self._loaded[cache_key] = loaded
        return loaded

    def load_all(self, module_paths: Optional[List[str]] = None) -> List[LoadedTool]:
        """Load all discovered tools or a specific list."""
        paths = module_paths or self.discover()
        loaded = []
        for path in paths:
            entry = self.load(path)
            if entry:
                loaded.append(entry)
        return loaded

    def _find_tool_class(self, module, class_name: str) -> Optional[Type[BaseTool]]:
        """Find a BaseTool subclass in a module."""
        if class_name:
            candidate = getattr(module, class_name, None)
            if candidate and issubclass(candidate, BaseTool) and candidate is not BaseTool:
                return candidate
            return None
        for attr_name in dir(module):
            candidate = getattr(module, attr_name)
            try:
                if isinstance(candidate, type) and issubclass(candidate, BaseTool) and candidate is not BaseTool:
                    return candidate
            except TypeError:
                continue
        return None
