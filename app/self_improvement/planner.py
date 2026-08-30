"""Self-improvement improvement planner.

Converts system analysis into a prioritized improvement plan with
executable tasks.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.ai.ai_manager import AIManager
from app.core.logger import Logger


IMPROVEMENT_PLAN_PROMPT = """
You are a senior software engineering lead.

Given the following system analysis, create a prioritized improvement plan.

Analysis:
{analysis}

Create a plan with:
1. High priority improvements (must fix)
2. Medium priority improvements (should fix)
3. Low priority improvements (nice to have)

For each improvement:
- title: short description
- type: one of [refactor, bug, performance, security, documentation, testing]
- file: target file path
- reason: why this improvement is needed
- approach: how to implement it
- risk: one of [low, medium, high]
- effort: one of [low, medium, high]

Return ONLY valid JSON.

Schema:
{{
  "high_priority": [],
  "medium_priority": [],
  "low_priority": [],
  "summary": "",
  "estimated_total_effort": ""
}}
"""


@dataclass
class ImprovementTask:
    """Single improvement task."""

    id: str
    title: str
    type: str
    file: str
    reason: str
    approach: str
    risk: str
    effort: str
    priority: str = "medium"
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "file": self.file,
            "reason": self.reason,
            "approach": self.approach,
            "risk": self.risk,
            "effort": self.effort,
            "priority": self.priority,
            "status": self.status,
            "metadata": dict(self.metadata),
        }


@dataclass
class ImprovementPlan:
    """Complete improvement plan."""

    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    high_priority: List[ImprovementTask] = field(default_factory=list)
    medium_priority: List[ImprovementTask] = field(default_factory=list)
    low_priority: List[ImprovementTask] = field(default_factory=list)
    summary: str = ""
    estimated_total_effort: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "high_priority": [t.to_dict() for t in self.high_priority],
            "medium_priority": [t.to_dict() for t in self.medium_priority],
            "low_priority": [t.to_dict() for t in self.low_priority],
            "summary": self.summary,
            "estimated_total_effort": self.estimated_total_effort,
            "metadata": dict(self.metadata),
        }


class ImprovementPlanner:
    """Generate improvement plans from system analysis."""

    def __init__(self, ai=None):
        self.ai = ai or AIManager()

    def create_plan(self, analysis: Dict[str, Any]) -> ImprovementPlan:
        """Create an improvement plan from analysis results."""
        Logger.info("[ImprovementPlanner] Creating improvement plan")
        
        # Try LLM-based planning first
        try:
            return self._llm_plan(analysis)
        except Exception as exc:
            Logger.warning(f"[ImprovementPlanner] LLM planning failed: {exc}")
        
        # Fallback to rule-based planning
        return self._rule_based_plan(analysis)

    def _llm_plan(self, analysis: Dict[str, Any]) -> ImprovementPlan:
        """Use LLM to generate improvement plan."""
        prompt = IMPROVEMENT_PLAN_PROMPT.format(analysis=json.dumps(analysis, indent=2, default=str))
        response = self.ai.ask(prompt)
        
        # Parse response
        cleaned = response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        data = json.loads(cleaned)
        plan = ImprovementPlan(
            summary=data.get("summary", ""),
            estimated_total_effort=data.get("estimated_total_effort", ""),
        )
        
        for priority, task_list in [("high", data.get("high_priority", [])), 
                                     ("medium", data.get("medium_priority", [])),
                                     ("low", data.get("low_priority", []))]:
            for i, task_data in enumerate(task_list):
                task = ImprovementTask(
                    id=f"{priority}-{i+1}",
                    title=task_data.get("title", ""),
                    type=task_data.get("type", "refactor"),
                    file=task_data.get("file", ""),
                    reason=task_data.get("reason", ""),
                    approach=task_data.get("approach", ""),
                    risk=task_data.get("risk", "medium"),
                    effort=task_data.get("effort", "medium"),
                    priority=priority,
                )
                if priority == "high":
                    plan.high_priority.append(task)
                elif priority == "medium":
                    plan.medium_priority.append(task)
                else:
                    plan.low_priority.append(task)
        
        return plan

    def _rule_based_plan(self, analysis: Dict[str, Any]) -> ImprovementPlan:
        """Rule-based fallback planning."""
        plan = ImprovementPlan(summary="Rule-based improvement plan")
        
        # Convert analysis opportunities to tasks
        opportunities = analysis.get("improvement_opportunities", [])
        for opp in opportunities:
            priority = opp.get("priority", "medium")
            task = ImprovementTask(
                id=opp.get("id", f"task-{len(plan.high_priority)+len(plan.medium_priority)+len(plan.low_priority)+1}"),
                title=opp.get("message", opp.get("rule", "Improvement")),
                type=opp.get("type", "refactor"),
                file=opp.get("file", ""),
                reason=opp.get("message", ""),
                approach=opp.get("suggestion", ""),
                risk=self._estimate_risk(opp),
                effort=opp.get("estimated_effort", "medium"),
                priority=priority,
            )
            
            if priority == "high":
                plan.high_priority.append(task)
            elif priority == "medium":
                plan.medium_priority.append(task)
            else:
                plan.low_priority.append(task)
        
        plan.summary = f"Found {len(plan.high_priority)} high, {len(plan.medium_priority)} medium, {len(plan.low_priority)} low priority improvements"
        plan.estimated_total_effort = self._estimate_total_effort(plan)
        
        return plan

    @staticmethod
    def _estimate_risk(task_data: Dict[str, Any]) -> str:
        """Estimate risk of an improvement task."""
        severity = task_data.get("severity", "medium")
        if severity in ("critical", "high"):
            return "high"
        elif severity == "medium":
            return "medium"
        return "low"

    @staticmethod
    def _estimate_total_effort(plan: ImprovementPlan) -> str:
        """Estimate total effort for the plan."""
        total = len(plan.high_priority) * 3 + len(plan.medium_priority) * 2 + len(plan.low_priority) * 1
        if total > 20:
            return "high"
        elif total > 10:
            return "medium"
        return "low"
