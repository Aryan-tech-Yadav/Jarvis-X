class AgentCapabilityMatcher:
    def score(self, agent, task):
        requested = str(getattr(task, "agent", getattr(task, "title", task))).casefold()
        capabilities = getattr(agent, "capabilities", [getattr(agent, "name", "")])
        match = max((requested in str(value).casefold() for value in capabilities), default=False)
        return (1 if match else 0) + getattr(agent, "priority", 0) / 100

    def best(self, agents, task):
        return max(agents, key=lambda agent: self.score(agent, task), default=None)