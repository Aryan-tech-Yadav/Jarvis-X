from app.agents.agent_status import AgentStatus


class AgentHealthMonitor:
    def __init__(self):
        self.statuses = {}

    def update(self, name, status):
        value = status.value if isinstance(status, AgentStatus) else status
        self.statuses[name] = value

    def get(self, name):
        return self.statuses.get(name, AgentStatus.IDLE.value)

    def snapshot(self):
        return dict(self.statuses)