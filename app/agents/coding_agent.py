from app.agents.base_agent import BaseAgent


class CodingAgent(BaseAgent):
    name = "coding"

    def run(self, context):
        context.shared_notes["coding"] = "Code generation and refactoring delegated to coding agent."
        return {"success": True, "output": context.shared_notes["coding"]}