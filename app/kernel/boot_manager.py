from inspect import signature

from app.core.registry import ModuleRegistry
from app.core.results import ExecutionResult


class KernelBootManager:
    """Starts explicitly registered kernel components in deterministic order."""

    ORDER = ("event_bus", "runtime", "resource_manager", "monitor", "dispatcher", "scheduler")

    def __init__(self, registry=None, configuration=None):
        self.registry = registry or ModuleRegistry()
        self.configuration = dict(configuration or {})
        self.booted = False

    def boot(self, context=None):
        initialized = []
        try:
            names = [name for name in self.ORDER if self.registry.get(name) is not None]
            names.extend(name for name in self.registry.names() if name not in names)
            for name in names:
                component = self.registry.get(name)
                hook = getattr(component, "initialize", None)
                if callable(hook):
                    value = self._invoke(hook, context)
                    if value is False:
                        raise RuntimeError("Component rejected initialization: " + name)
                initialized.append(name)
            self.booted = True
            return ExecutionResult.completed({"components": initialized, "configuration": dict(self.configuration)}, "Kernel boot complete")
        except Exception as error:
            self.booted = False
            return ExecutionResult.failed(str(error), data={"components": initialized})

    def shutdown(self, context=None):
        errors = []
        for name in reversed(self.registry.names()):
            hook = getattr(self.registry.get(name), "shutdown", None)
            if callable(hook):
                try:
                    self._invoke(hook, context)
                except Exception as error:
                    errors.append(name + ": " + str(error))
        self.booted = False
        return ExecutionResult.completed(message="Kernel shutdown complete", warnings=errors) if not errors else \
            ExecutionResult.failed("Kernel shutdown completed with errors", errors=errors)

    @staticmethod
    def _invoke(hook, context):
        return hook(context) if len(signature(hook).parameters) else hook()
