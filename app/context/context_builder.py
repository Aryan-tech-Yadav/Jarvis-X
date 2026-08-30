class ContextBuilder:
    def build(self, goal, current_project=None, current_step="", conversation=None,
              reasoning=None, progress=None, plan=None, project_summary=None):
        return {
            "goal": goal,
            "project": current_project,
            "current_step": current_step,
            "conversation": conversation or [],
            "reasoning": reasoning or [],
            "progress": progress or {},
            "plan": plan,
            "project_summary": project_summary,
        }