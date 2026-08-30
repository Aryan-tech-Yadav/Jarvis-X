from abc import ABC, abstractmethod
from collections.abc import Mapping


class BaseAgent(ABC):
    """Small, stable contract shared by every collaborating agent.

    ``run`` is retained for the original Jarvis agents.  New agents implement the
    same method and are invoked through :meth:`execute`, which keeps the public
    API described by the multi-agent milestone consistent.
    """

    agent_id = "agent"
    capabilities = ()

    def name(self):
        """Return the registry name for agents using the new API."""
        return self.agent_id

    def can_handle(self, task):
        """Return whether this agent advertises support for *task*."""
        if isinstance(task, Mapping):
            requested = task.get("agent") or task.get("type") or task.get("operation") or task.get("goal", "")
        else:
            requested = getattr(task, "agent", getattr(task, "type", task))
        requested = str(requested).casefold()
        supported = {self.agent_id.casefold(), *(str(item).casefold() for item in self.capabilities)}
        return any(item in requested or requested in item for item in supported if item)

    @staticmethod
    def context_value(context, key, default=None):
        return context.get(key, default) if isinstance(context, Mapping) else getattr(context, key, default)

    @staticmethod
    def update_context(context, key, value):
        if isinstance(context, Mapping):
            context[key] = value
        else:
            setattr(context, key, value)
        return value

    def plan(self, context):
        return {"success": True, "output": context}

    def execute(self, task):
        return self.run(task)

    def review(self, context):
        return {"success": True, "output": context}

    def report(self, context):
        return {"success": True, "output": context}

    def initialize(self, context=None):
        return True

    def cleanup(self, context=None):
        return True

    @abstractmethod
    def run(self, context):
        """Return a dictionary containing at least ``success`` and ``output``."""
