class ModuleRegistry:
    """Small dependency-injection registry for explicitly provided modules."""

    def __init__(self):
        self._modules = {}

    def register(self, name, module=None):
        if module is None:
            module = name
            name = module.__class__.__name__
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Module name cannot be empty")
        self._modules[name.strip()] = module
        return module

    def get(self, name, default=None):
        return self._modules.get(name, default)

    def require(self, name):
        module = self.get(name)
        if module is None:
            raise KeyError(f"Module not registered: {name}")
        return module

    def names(self):
        return tuple(self._modules)
