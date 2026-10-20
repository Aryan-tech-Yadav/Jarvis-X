"""EOS kernel facade that dispatches work through registered agents."""

from app.eos.dispatcher import Dispatcher
from app.eos.event_bus import EventBus
from app.eos.registry import AgentRegistry
from app.eos.result import AgentResult
from app.eos.telemetry import Telemetry
from app.eos.events import TASK_COMPLETED, TASK_CREATED, TASK_FAILED, TASK_STARTED


class EOSKernel:
    def __init__(self, registry=None, event_bus=None, telemetry=None):
        self.registry = registry or AgentRegistry()
        self.event_bus = event_bus or EventBus()
        self.telemetry = telemetry or Telemetry()
        self.dispatcher = Dispatcher(self.registry)

    def execute(self, task) -> AgentResult:
        self.event_bus.publish(TASK_CREATED, task)
        self.event_bus.publish(TASK_STARTED, task)
        result = self.dispatcher.dispatch(task)
        event = TASK_COMPLETED if result.success else TASK_FAILED
        self.event_bus.publish(event, result)
        self.telemetry.record(event, agent=result.agent, success=result.success)
        return result
