class DashboardData:
    def collect(self, **values):
        defaults = {
            "projects": 0, "successes": 0, "failures": 0, "repairs": 0,
            "learning_events": 0, "memory_entries": 0, "reasoning_calls": 0,
            "tool_calls": 0, "knowledge_hits": 0, "skills": 0,
        }
        defaults.update({key: value for key, value in values.items() if value is not None})
        return defaults
