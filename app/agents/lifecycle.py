"""Lifecycle manager for dynamically registered agents."""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from .dynamic_loader import AgentLoader

if TYPE_CHECKING:
    from app.eos.registry import AgentRegistry


class AgentLifecycleManager:
    def __init__(self, registry: Optional["AgentRegistry"] = None, loader: Optional[AgentLoader] = None):
        if registry is None:
            from app.eos.registry import AgentRegistry
            registry = AgentRegistry()
        self.registry = registry
        self.loader = loader or AgentLoader()
        self._sources: Dict[str, tuple[str, str]] = {}

    def load(self, module_path: str, class_name: str, **kwargs: Any) -> Any:
        agent = self.loader.instantiate(module_path, class_name, **kwargs)
        self.registry.register(agent)
        name = self.registry._name_for(agent)
        self._sources[name] = (module_path, class_name)
        initialize = getattr(agent, "initialize", None)
        if callable(initialize) and not bool(initialize()):
            self.registry.unregister(name)
            self._sources.pop(name, None)
            raise RuntimeError(f"Agent failed to initialize: {name}")
        return agent

    def unload(self, name: str) -> Any:
        agent = self.registry.get(name)
        if agent is None:
            return None
        shutdown = getattr(agent, "shutdown", None)
        if callable(shutdown) and not bool(shutdown()):
            raise RuntimeError(f"Agent failed to shut down: {name}")
        self._sources.pop(name, None)
        return self.registry.unregister(name)

    def spawn(self, agent: Any) -> Any:
        self.registry.register(agent)
        initialize = getattr(agent, "initialize", None)
        if callable(initialize) and not bool(initialize()):
            name = self.registry._name_for(agent)
            self.registry.unregister(name)
            raise RuntimeError(f"Agent failed to initialize: {name}")
        return agent

    def hot_reload(self, name: str) -> Any:
        source = self._sources.get(name)
        if source is None:
            raise KeyError(f"No source metadata for agent: {name}")
        module_path, class_name = source
        self.unload(name)
        self.loader.reload(module_path)
        return self.load(module_path, class_name)

    def metadata(self) -> list[dict]:
        metadata = []
        for item in self.registry.list_metadata():
            name = item["name"]
            agent = self.registry.get(name)
            health_report = getattr(agent, "health_report", None)
            report = health_report() if callable(health_report) else None
            item["priority"] = getattr(agent, "priority", 0)
            item["dependencies"] = list(getattr(agent, "dependencies", ()))
            item["permissions"] = list(getattr(agent, "permissions", ()))
            item["status"] = str(getattr(agent, "status", "unknown"))
            if report is not None:
                item["health"] = getattr(getattr(report, "status", None), "value", str(report))
            else:
                item["health"] = "healthy" if item["healthy"] else "unhealthy"
            metadata.append(item)
        return metadata

    def find_by_capability(self, capability: str) -> list[Any]:
        return self.registry.find_by_capability(capability)
