"""Post-execution reflection contract."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Reflection:
    outcome: str
    lessons: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"outcome": self.outcome, "lessons": list(self.lessons),
                "improvements": list(self.improvements)}


class Reflector:
    def reflect(self, goal: str, result: Any) -> Reflection:
        success = bool(result.get("success")) if isinstance(result, dict) else bool(result)
        outcome = "success" if success else "failure"
        lessons = ["Reuse the validated plan"] if success else ["Inspect the failure before retrying"]
        return Reflection(outcome, lessons=lessons)

