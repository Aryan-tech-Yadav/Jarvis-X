class PatternExtractor:
    def extract(self, context):
        data = context.as_dict() if hasattr(context, "as_dict") else dict(context)
        validation = data.get("validation", {})
        critic = data.get("critic", {})
        progress = data.get("progress", [])
        return {
            "goal": data.get("goal", ""),
            "summary": self._summary(data),
            "agent_sequence": [item.get("agent") for item in progress if item.get("agent")],
            "plan": data.get("plan"),
            "files": data.get("files", []),
            "validation": validation.get("output", "") if isinstance(validation, dict) else validation,
            "critic_score": critic.get("score") if isinstance(critic, dict) else None,
        }

    def _summary(self, data):
        return "Completed task with " + str(len(data.get("files", []))) + " indexed files."