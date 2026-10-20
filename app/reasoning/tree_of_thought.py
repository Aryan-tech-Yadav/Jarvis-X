"""Deterministic Tree-of-Thought branch generation and selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .working_memory import WorkingMemory, build_working_memory


@dataclass(frozen=True)
class ThoughtBranch:
    branch_id: str
    approach: str
    steps: List[str]
    score: float
    rationale: str
    pruned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "approach": self.approach,
            "steps": list(self.steps),
            "score": self.score,
            "rationale": self.rationale,
            "pruned": self.pruned,
        }


@dataclass(frozen=True)
class ThoughtTreeResult:
    goal: str
    working_memory: WorkingMemory
    branches: List[ThoughtBranch]
    selected_branch_id: Optional[str]

    @property
    def selected(self) -> Optional[ThoughtBranch]:
        return next(
            (branch for branch in self.branches if branch.branch_id == self.selected_branch_id),
            None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "working_memory": self.working_memory.to_dict(),
            "branches": [branch.to_dict() for branch in self.branches],
            "selected_branch_id": self.selected_branch_id,
            "selected": self.selected.to_dict() if self.selected else None,
        }


class TreeOfThoughtEngine:
    """Generate alternatives, score them, and prune weak branches."""

    def explore(
        self,
        goal: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        branch_builder: Optional[Callable[[str, WorkingMemory], List[ThoughtBranch]]] = None,
        max_branches: int = 3,
        min_score: float = 0.45,
    ) -> ThoughtTreeResult:
        if max_branches < 1:
            raise ValueError("max_branches must be positive")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1")
        memory = build_working_memory(goal, context)
        branches = (
            branch_builder(memory.goal, memory)
            if branch_builder
            else self._default_branches(memory)
        )
        ranked = sorted(branches[:max_branches], key=lambda item: item.score, reverse=True)
        normalized = []
        for branch in ranked:
            score = max(0.0, min(1.0, float(branch.score)))
            normalized.append(ThoughtBranch(
                branch.branch_id,
                branch.approach,
                list(branch.steps),
                score,
                branch.rationale,
                pruned=score < min_score,
            ))
        viable = [branch for branch in normalized if not branch.pruned]
        return ThoughtTreeResult(
            memory.goal,
            memory,
            normalized,
            viable[0].branch_id if viable else None,
        )

    @staticmethod
    def _default_branches(memory: WorkingMemory) -> List[ThoughtBranch]:
        goal = memory.goal
        risky = bool(memory.risks) or any(
            word in goal.casefold() for word in ("production", "deploy", "delete", "migration")
        )
        return [
            ThoughtBranch(
                "branch-validate-first",
                "validate-first",
                ["Clarify requirements", "Validate constraints", "Proceed with the smallest safe change"],
                0.82 if not risky else 0.9,
                "Prioritizes correctness and explicit constraints.",
            ),
            ThoughtBranch(
                "branch-research-first",
                "research-first",
                ["Retrieve relevant experience", "Compare viable approaches", "Select evidence-backed approach"],
                0.72 if memory.unknowns else 0.58,
                "Reduces uncertainty before committing to an approach.",
            ),
            ThoughtBranch(
                "branch-fast-path",
                "fast-path",
                ["Use the simplest compatible approach", "Run focused verification"],
                0.62 if not risky else 0.35,
                "Optimizes speed when risk and uncertainty are low.",
            ),
        ]
