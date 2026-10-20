class PluginManager:
    def __init__(self):
        self._plugins = {}

    def register(self, plugin):
        name = getattr(plugin, "name", "")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Plugin must have a name")
        if name in self._plugins:
            raise ValueError(f"Plugin already registered: {name}")
        for method in ("initialize", "shutdown", "tools", "metadata"):
            if not callable(getattr(plugin, method, None)):
                raise TypeError(f"Plugin must provide {method}()")
        plugin.initialize()
        self._plugins[name] = plugin
        return plugin

    def unregister(self, name):
        plugin = self._plugins.pop(name, None)
        if plugin:
            plugin.shutdown()
        return plugin

    def get(self, name):
        return self._plugins.get(name)

    def list_plugins(self):
        return list(self._plugins.values())