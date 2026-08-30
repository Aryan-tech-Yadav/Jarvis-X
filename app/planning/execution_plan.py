from dataclasses import dataclass, field


@dataclass
class ExecutionPlan:
    goal: str
    steps: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        goal = data.get("goal", "")
        steps = data.get("steps", [])
        if not isinstance(goal, str) or not isinstance(steps, list):
            raise ValueError("Invalid execution plan")
        clean_steps = [step.strip() for step in steps if isinstance(step, str) and step.strip()]
        if not goal.strip() or not clean_steps:
            raise ValueError("Execution plan must contain a goal and at least one step")
        return cls(goal=goal.strip(), steps=clean_steps)

    def to_dict(self):
        return {"goal": self.goal, "steps": self.steps}
