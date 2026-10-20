"""EOS agent registry with capability-based lookup."""

from typing import Any, List, Optional

from app.agents.agent_registry import AgentRegistry as LegacyAgentRegistry


class AgentRegistry(LegacyAgentRegistry):
    """Register enabled agents and resolve them by name or capability."""

    def register(self, agent: Any, legacy_agent: Any = None) -> None:
        super().register(agent, legacy_agent)

    def unregister(self, name: str) -> Optional[Any]:
        return super().unregister(name)

    def get(self, name: str) -> Optional[Any]:
        return super().get(name)

    def list(self) -> List[str]:
        return self.list_agents()

    def list_metadata(self) -> List[dict]:
        """Return safe inspectable metadata for registered agents."""
        return [
            {
                "name": self._name_for(agent),
                "version": str(getattr(agent, "version", "1.0")),
                "capabilities": list(getattr(agent, "capabilities", ())),
                "enabled": bool(getattr(agent, "enabled", True)),
                "healthy": self._healthy(agent),
            }
            for agent in self._agents.values()
        ]

    def find(self, query: Any) -> Optional[Any]:
        """Resolve an agent by registered name or advertised capability."""
        if isinstance(query, str) and query in self._agents:
            return self.get(query)
        capability = query if isinstance(query, str) else getattr(query, "capability", "")
        if isinstance(query, dict):
            capability = query.get("capability", "")
        matches = self.find_by_capability(capability) if capability else []
        return matches[0] if matches else super().find(query)

    def find_by_capability(self, capability: str) -> List[Any]:
        requested = capability.casefold()
        return [
            agent for agent in self._agents.values()
            if requested in {
                str(value).casefold()
                for value in getattr(agent, "capabilities", ())
            }
            and getattr(agent, "enabled", True)
            and self._healthy(agent)
        ]

    @staticmethod
    def _healthy(agent: Any) -> bool:
        check = getattr(agent, "health_check", None)
        return bool(check()) if callable(check) else True


__all__ = ["AgentRegistry"]
