"""Standard AMOS agent contract."""

from abc import abstractmethod
from typing import Any, List

from app.eos.base_agent import AgentStatus, BaseAgent
from app.eos.result import AgentResult
from app.agents.ecosystem.config import AgentConfig
from app.agents.ecosystem.health import HealthReport, HealthStatus
from app.agents.ecosystem.memory import AgentMemory
from app.agents.ecosystem.metrics import AgentMetrics


class EcosystemAgent(BaseAgent):
    """EOS BaseAgent with learning, reflection, memory, and metrics hooks."""

    def __init__(self, config: AgentConfig | None = None):
        super().__init__()
        self.config = config or AgentConfig()
        self.enabled = self.config.enabled
        self.memory = AgentMemory()
        self.metrics = AgentMetrics()
        self._reflections: List[Any] = []

    def health_report(self) -> HealthReport:
        status = HealthStatus.HEALTHY if self.health_check() else HealthStatus.UNHEALTHY
        return HealthReport(status, f"{self.name} is {status.value}")

    def learn(self, lesson: Any) -> None:
        self.memory.remember(lesson)

    def reflect(self, reflection: Any) -> None:
        self._reflections.append(reflection)

    def reflection_snapshot(self) -> List[Any]:
        return list(self._reflections)

