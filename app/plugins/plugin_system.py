"""Enhanced plugin system for dynamic agent/tool extensions.

Plugins are discovered from the plugins/ directory and can add new
agents, tools, or capabilities without modifying core code.
"""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PluginManifest:
    """Plugin metadata and configuration."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": list(self.dependencies),
            "capabilities": list(self.capabilities),
            "enabled": self.enabled,
        }


class Plugin:
    """Base plugin class that all plugins must extend."""

    name = "plugin"
    version = "1.0.0"
    description = ""
    author = ""
    dependencies: List[str] = []
    capabilities: List[str] = []

    def initialize(self, plugin_manager) -> bool:
        """Called when plugin is loaded."""
        return True

    def shutdown(self) -> bool:
        """Called when plugin is unloaded."""
        return True

    def tools(self) -> List[Any]:
        """Return list of tools provided by this plugin."""
        return []

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "capabilities": self.capabilities,
        }


class PluginManager:
    """Enhanced plugin manager with discovery and lifecycle management."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self._plugins: Dict[str, Plugin] = {}
        self._manifests: Dict[str, PluginManifest] = {}

    def register(self, plugin: Plugin) -> Plugin:
        """Register a plugin instance."""
        name = getattr(plugin, "name", "")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Plugin must have a name")
        if name in self._plugins:
            raise ValueError(f"Plugin already registered: {name}")
        
        # Validate plugin interface
        for method in ("initialize", "shutdown", "tools", "metadata"):
            if not callable(getattr(plugin, method, None)):
                raise TypeError(f"Plugin must provide {method}()")
        
        plugin.initialize(self)
        self._plugins[name] = plugin
        self._manifests[name] = PluginManifest(
            name=name,
            version=getattr(plugin, "version", "1.0.0"),
            description=getattr(plugin, "description", ""),
            author=getattr(plugin, "author", ""),
            dependencies=list(getattr(plugin, "dependencies", [])),
            capabilities=list(getattr(plugin, "capabilities", [])),
        )
        return plugin

    def unregister(self, name: str) -> Optional[Plugin]:
        """Unregister a plugin."""
        plugin = self._plugins.pop(name, None)
        if plugin:
            plugin.shutdown()
            self._manifests.pop(name, None)
        return plugin

    def get(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins with their metadata."""
        return [manifest.to_dict() for manifest in self._manifests.values()]

    def get_capabilities(self) -> List[str]:
        """Get all capabilities from all plugins."""
        capabilities = []
        for manifest in self._manifests.values():
            capabilities.extend(manifest.capabilities)
        return list(set(capabilities))

    def load_plugins(self, path: Optional[str] = None) -> List[Plugin]:
        """Dynamically load plugins from directory."""
        search_path = path or self.plugins_dir
        loaded = []
        if not os.path.isdir(search_path):
            return loaded
        
        for root, _, files in os.walk(search_path):
            for filename in files:
                if not filename.endswith(".py") or filename.startswith("_"):
                    continue
                module_path = os.path.join(root, filename)
                spec = importlib.util.spec_from_file_location(f"jarvis_plugin_{filename}", module_path)
                if not spec or not spec.loader:
                    continue
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except Exception:
                    continue
                plugin_class = getattr(module, "Plugin", None)
                if plugin_class:
                    try:
                        loaded.append(self.register(plugin_class()))
                    except (TypeError, ValueError):
                        continue
        return loaded

    def has_capability(self, capability: str) -> bool:
        """Check if any plugin provides a capability."""
        return any(
            capability in manifest.capabilities
            for manifest in self._manifests.values()
        )
