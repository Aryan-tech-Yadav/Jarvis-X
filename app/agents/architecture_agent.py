from app.agents.base_agent import BaseAgent


class ArchitectureAgent(BaseAgent):
    name = "architecture"

    def run(self, context):
        context.shared_notes["architecture"] = "Architecture review requested."
        return {"success": True, "output": context.shared_notes["architecture"]}