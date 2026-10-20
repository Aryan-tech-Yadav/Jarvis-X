from app.agents.base_agent import BaseAgent


class DebugAgent(BaseAgent):
    name = "debug"

    def run(self, context):
        context.shared_notes["debug"] = "Debug analysis requested."
        return {"success": True, "output": context.shared_notes["debug"]}