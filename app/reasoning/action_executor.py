from app.tools.tool_manager import ToolManager
from app.reasoning.observation import Observation
from time import perf_counter


class ActionExecutor:
    def __init__(self, tool_manager=None, metrics=None, event_bus=None):
        self.tool_manager = tool_manager or ToolManager()
        self.metrics = metrics
        self.event_bus = event_bus

    def execute(self, action):
        if not action or not action.tool:
            return Observation(False, "", "Action has no tool")
        arguments = dict(action.arguments or {})
        started = perf_counter()
        if self.event_bus:
            self.event_bus.publish("ACTION_STARTED", {"tool": action.tool, "action": action.action})
        try:
            result = self.tool_manager.execute(action.tool, action.action, **arguments)
            observation = Observation(bool(result.get("success")), result.get("output"), result.get("error"), action.tool, action.action)
        except Exception as error:
            observation = Observation(False, "", str(error), action.tool, action.action)
        if self.metrics:
            self.metrics.record("tool_calls")
            if not observation.success:
                self.metrics.record("failures")
            self.metrics.record_runtime(perf_counter() - started)
        if self.event_bus:
            self.event_bus.publish("ACTION_FINISHED", observation.to_dict())
        return observation