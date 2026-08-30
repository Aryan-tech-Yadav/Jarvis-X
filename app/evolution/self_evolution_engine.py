"""Self Evolution Engine facade over the existing ALE learning components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .learning_engine import AutonomousLearningEngine
from .models.experience import ExecutionMetrics
from .models.failure import FailureCategory


@dataclass
class AgentSkill:
    agent: str
    xp: int = 0
    successes: int = 0
    failures: int = 0

    @property
    def level(self) -> int:
        return self.xp // 100 + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "xp": self.xp,
            "level": self.level,
            "successes": self.successes,
            "failures": self.failures,
        }


class SelfEvolutionEngine:
    """Run reflection, rule generation, and measurable skill updates after a project."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.learning = AutonomousLearningEngine(knowledge_dir)
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.prompt_updates: List[Dict[str, Any]] = []
        self.skills: Dict[str, AgentSkill] = {}

    def process_project(
        self,
        project_name: str,
        *,
        result: str = "SUCCESS",
        execution_time_sec: float = 0.0,
        quality_score: float = 0.0,
        test_coverage: float = 0.0,
        repair_count: int = 0,
        domain: str = "general",
        architecture: str = "standard",
        stack: Optional[List[str]] = None,
        agent: str = "engineering",
        failures: Optional[List[Dict[str, Any]]] = None,
        lessons: Optional[List[str]] = None,
        metrics: Optional[ExecutionMetrics] = None,
    ) -> Dict[str, Any]:
        """Record one run and derive reusable improvements from its outcome."""
        if not project_name or not project_name.strip():
            raise ValueError("Project name cannot be empty")
        normalized_result = result.upper()
        if normalized_result not in {"SUCCESS", "FAILED", "PARTIAL"}:
            raise ValueError("Result must be SUCCESS, FAILED, or PARTIAL")

        failure_items = list(failures or [])
        experience = self.learning.process_project_completion(
            project_name=project_name.strip(),
            execution_time_sec=max(0.0, execution_time_sec),
            quality_score=quality_score,
            test_coverage=test_coverage,
            repair_count=max(0, repair_count),
            result=normalized_result,
            domain=domain,
            architecture=architecture,
            stack=stack,
            metrics=metrics,
            failures_encountered=failure_items,
            lessons=lessons,
        )
        success = normalized_result == "SUCCESS"
        skill = self.skills.setdefault(agent, AgentSkill(agent))
        skill.xp += 10 if success else 1
        skill.successes += int(success)
        skill.failures += int(not success)

        generated_rules = self._generate_rules(project_name, failure_items)
        prompt_updates = self._update_prompts(project_name, failure_items)
        return {
            "experience": experience["experience"],
            "reflection": {
                "lessons": list(lessons or []),
                "failure_count": len(failure_items),
                "recommendations": experience["recommendations"],
            },
            "rules": generated_rules,
            "prompt_updates": prompt_updates,
            "skill": skill.to_dict(),
            "evolution_score": experience["evolution_score"],
        }

    def dashboard(self) -> Dict[str, Any]:
        """Return current learning, rule, prompt, and skill metrics."""
        return {
            "learning": self.learning.get_evolution_dashboard(),
            "rules_learned": len(self.rules),
            "prompt_updates": len(self.prompt_updates),
            "skills": [skill.to_dict() for skill in self.skills.values()],
        }

    def _generate_rules(self, project_name: str, failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        generated = []
        for failure in failures:
            category = str(failure.get("category", FailureCategory.GENERAL.value))
            rule_id = f"rule-{category}"
            rule = self.rules.setdefault(rule_id, {
                "rule_id": rule_id,
                "condition": f"when failure category is {category}",
                "action": failure.get("fix_strategy") or "Add validation and a regression test.",
                "observations": 0,
            })
            rule["observations"] += 1
            rule["last_project"] = project_name
            generated.append(dict(rule))
        return generated

    def _update_prompts(self, project_name: str, failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        updates = []
        for failure in failures:
            update = {
                "project": project_name,
                "append": failure.get("fix_strategy") or "Include tests, validation, and operational documentation.",
                "reason": failure.get("reason", failure.get("category", "failure")),
            }
            self.prompt_updates.append(update)
            updates.append(dict(update))
        return updates
