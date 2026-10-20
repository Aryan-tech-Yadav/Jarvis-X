class ContextBuilder:
    def build(self, state, project=None, progress=None, conversation_summary=""):
        return {
            "goal": state.goal,
            "history": state.history(),
            "project": project,
            "progress": progress or {},
            "conversation_summary": conversation_summary,
        }