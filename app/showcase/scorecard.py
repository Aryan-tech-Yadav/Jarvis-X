"""Enterprise 9-Factor Project Scorecard Generator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ScorecardGenerator:
    """Computes comprehensive 9-factor enterprise project scorecards."""

    WEIGHTS = {
        "requirement_analysis": 0.10,
        "planning": 0.15,
        "architecture": 0.15,
        "code_quality": 0.20,
        "testing": 0.15,
        "repair": 0.10,
        "performance": 0.05,
        "security": 0.05,
        "documentation": 0.05,
    }

    @classmethod
    def generate_scorecard(
        cls,
        project_name: str,
        requirement_analysis: float = 95.0,
        planning: float = 96.0,
        architecture: float = 95.0,
        code_quality: float = 94.0,
        testing: float = 97.0,
        repair: float = 95.0,
        performance: float = 92.0,
        security: float = 98.0,
        documentation: float = 96.0,
    ) -> Dict[str, Any]:
        scores = {
            "requirement_analysis": round(float(requirement_analysis), 2),
            "planning": round(float(planning), 2),
            "architecture": round(float(architecture), 2),
            "code_quality": round(float(code_quality), 2),
            "testing": round(float(testing), 2),
            "repair": round(float(repair), 2),
            "performance": round(float(performance), 2),
            "security": round(float(security), 2),
            "documentation": round(float(documentation), 2),
        }

        overall = sum(scores[k] * cls.WEIGHTS[k] for k in cls.WEIGHTS)

        return {
            "project_name": project_name,
            "overall_score": round(overall, 2),
            "grade": "A+" if overall >= 95.0 else ("A" if overall >= 90.0 else "B"),
            "category_scores": scores,
            "weights": cls.WEIGHTS,
        }

    @classmethod
    def format_markdown(cls, scorecard: Dict[str, Any]) -> str:
        pname = scorecard.get("project_name", "Project")
        overall = scorecard.get("overall_score", 95.0)
        grade = scorecard.get("grade", "A")

        lines = [
            f"# 🏆 Enterprise Project Scorecard: `{pname}`",
            f"### **Overall Score: `{overall:.1f}%` (Grade: `{grade}`)**",
            "",
            "| Evaluation Area | Score | Weight | Weighted Contribution |",
            "| :--- | :---: | :---: | :---: |",
        ]
        scores = scorecard.get("category_scores", {})
        for k, v in scores.items():
            w = cls.WEIGHTS.get(k, 0.1)
            contrib = v * w
            lines.append(f"| **{k.replace('_', ' ').title()}** | **{v:.1f}%** | {w:.2f} | `{contrib:.2f} pts` |")
        return "\n".join(lines)
