class GoalChecker:
    def is_complete(self, goal, completed_steps, required_steps=None):
        required = set(required_steps or [])
        return bool(goal) and required.issubset(set(completed_steps))