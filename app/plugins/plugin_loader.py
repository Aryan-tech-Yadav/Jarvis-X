import importlib.util
import os


class PluginLoader:
    def __init__(self, manager):
        self.manager = manager

    def load_plugins(self, path="plugins"):
        loaded = []
        if not os.path.isdir(path):
            return loaded
        for root, _, files in os.walk(path):
            for filename in files:
                if not filename.endswith(".py") or filename.startswith("_"):
                    continue
                module_path = os.path.join(root, filename)
                spec = importlib.util.spec_from_file_location("jarvis_plugin", module_path)
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
                        loaded.append(self.manager.register(plugin_class()))
                    except (TypeError, ValueError):
                        continue
        return loaded