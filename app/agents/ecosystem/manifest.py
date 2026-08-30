"""Data-driven AMOS agent catalog."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from app.eos.registry import AgentRegistry


@dataclass(frozen=True)
class AgentManifest:
    name: str
    capabilities: tuple[str, ...] = ()
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_agent(cls, agent: Any) -> "AgentManifest":
        name = getattr(agent, "name", getattr(agent, "agent_id", agent.__class__.__name__))
        if callable(name):
            name = name()
        return cls(
            name=str(name),
            capabilities=tuple(str(item) for item in getattr(agent, "capabilities", ())),
            version=str(getattr(agent, "version", "1.0")),
        )


class AgentEcosystem:
    """Own registry population and expose an inspectable agent catalog."""

    def __init__(self, registry: AgentRegistry | None = None):
        self.registry = registry or AgentRegistry()

    def register(self, agent: Any) -> AgentManifest:
        self.registry.register(agent)
        return AgentManifest.from_agent(agent)

    def register_many(self, agents: Iterable[Any]) -> List[AgentManifest]:
        return [self.register(agent) for agent in agents]

    def manifests(self) -> List[AgentManifest]:
        return [
            AgentManifest.from_agent(agent)
            for agent in self.registry._agents.values()
        ]

