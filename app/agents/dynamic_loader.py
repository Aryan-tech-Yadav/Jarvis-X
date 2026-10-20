"""Dynamic loading of agent classes from importable Python modules."""

from __future__ import annotations

import importlib
import sys
from typing import Any, Type


class AgentLoader:
    def load_class(self, module_path: str, class_name: str) -> Type[Any]:
        if not module_path or not module_path.strip():
            raise ValueError("Agent module path cannot be empty")
        module = importlib.import_module(module_path.strip())
        candidate = getattr(module, class_name, None)
        if not isinstance(candidate, type):
            raise TypeError(f"Agent class not found: {module_path}.{class_name}")
        if not callable(getattr(candidate, "execute", None)) and not callable(getattr(candidate, "run", None)):
            raise TypeError("Loaded agent must provide execute(task) or run(context)")
        return candidate

    def instantiate(self, module_path: str, class_name: str, **kwargs: Any) -> Any:
        return self.load_class(module_path, class_name)(**kwargs)

    def reload(self, module_path: str) -> Any:
        module = sys.modules.get(module_path) or importlib.import_module(module_path)
        return importlib.reload(module)

