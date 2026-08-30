from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ReasoningState:
    goal: str
    current_step: int = 0
    thoughts: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    iteration_count: int = 0
    completed: bool = False

    @property
    def current_iteration(self):
        return self.iteration_count

    @current_iteration.setter
    def current_iteration(self, value):
        self.iteration_count = value

    def add_thought(self, thought: Dict[str, Any]):
        self.thoughts.append(thought)
        self.current_step = thought.get("step", self.current_step)
        self.iteration_count = self.current_step

    def add_action(self, action: Dict[str, Any]):
        self.actions.append(action)

    def add_observation(self, observation: Dict[str, Any]):
        self.observations.append(observation)

    def history(self):
        entries = []
        for index, thought in enumerate(self.thoughts):
            action = self.actions[index] if index < len(self.actions) else None
            observation = self.observations[index] if index < len(self.observations) else None
            entries.append({"thought": thought, "action": action, "observation": observation})
        return entries