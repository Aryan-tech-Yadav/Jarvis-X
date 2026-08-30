from app.agents.agent_registry import AgentRegistry
from app.agents.agent_status import AgentStatus
from app.agents.agent_context import AgentContext


class AgentCoordinator:
    def __init__(self, registry=None, workflow=None):
        self.registry = registry or AgentRegistry()
        self.workflow = tuple(workflow or ("coding", "testing", "debug"))
        self.statuses = {}

    def execute(self, goal, context=None):
        context = context or AgentContext(goal=goal)
        results = []
        for name in self.workflow:
            agent = self.registry.get(name)
            if agent is None:
                return {"success": False, "agent": name, "error": f"Unknown agent: {name}", "results": results}
            self.statuses[name] = AgentStatus.WORKING.value
            agent.initialize(context)
            try:
                result = agent.run(context)
                success = bool(result.get("success")) if isinstance(result, dict) else False
                self.statuses[name] = AgentStatus.COMPLETED.value if success else AgentStatus.FAILED.value
            except Exception as error:
                result = {"success": False, "error": str(error)}
                self.statuses[name] = AgentStatus.FAILED.value
            agent.cleanup(context)
            results.append({"agent": name, "result": result})
            if not isinstance(result, dict) or not result.get("success"):
                return {"success": False, "agent": name, "results": results}
        return {"success": True, "results": results, "context": context}