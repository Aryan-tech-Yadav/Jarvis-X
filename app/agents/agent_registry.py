class AgentRegistry:
    def __init__(self):
        self._agents = {}

    def register(self, name, agent=None):
        """Register an agent.

        Both ``register("coder", agent)`` and the milestone-friendly
        ``register(agent)`` forms are supported.
        """
        if agent is None:
            agent = name
            name = self._name_for(agent)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Agent name cannot be empty")
        if not callable(getattr(agent, "execute", None)) and not callable(getattr(agent, "run", None)):
            raise TypeError("Agent must provide execute(task) or run(context)")
        self._agents[name.strip()] = agent

    def get(self, name):
        return self._agents.get(name)

    def unregister(self, name):
        return self._agents.pop(name, None)

    def exists(self, name):
        return name in self._agents

    def list_agents(self):
        return list(self._agents)

    def find(self, task):
        """Find an exact agent first, then one capable of handling a task."""
        if isinstance(task, str) and task in self._agents:
            return self.get(task)
        agent = self.find_best(task)
        return agent

    def replace(self, name, agent):
        if name not in self._agents:
            raise KeyError(f"Agent not registered: {name}")
        if not callable(getattr(agent, "execute", None)) and not callable(getattr(agent, "run", None)):
            raise TypeError("Agent must provide execute(task) or run(context)")
        self._agents[name] = agent

    def find_best(self, task):
        if isinstance(task, dict):
            requested = str(task.get("agent") or task.get("type") or task.get("title") or task).casefold()
        else:
            requested = str(getattr(task, "agent", getattr(task, "title", task))).casefold()
        candidates = []
        for name, agent in self._agents.items():
            can_handle = getattr(agent, "can_handle", None)
            if callable(can_handle) and can_handle(task):
                candidates.append((2, getattr(agent, "priority", 0), agent))
                continue
            capabilities = getattr(agent, "capabilities", [name])
            score = max((1 if requested in str(capability).casefold() else 0) for capability in capabilities)
            if score:
                candidates.append((score, getattr(agent, "priority", 0), agent))
        return max(candidates, key=lambda item: (item[0], item[1]))[2] if candidates else None

    @staticmethod
    def _name_for(agent):
        candidate = getattr(agent, "name", None)
        if callable(candidate):
            candidate = candidate()
        if isinstance(candidate, str) and candidate.strip():
            return candidate
        candidate = getattr(agent, "agent_id", None)
        if isinstance(candidate, str) and candidate.strip():
            return candidate
        raise ValueError("Agent must expose a non-empty name")

    def names(self):
        return tuple(self._agents)

    def __contains__(self, name):
        return name in self._agents
