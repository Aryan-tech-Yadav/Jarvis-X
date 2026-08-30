"""Complexity estimator for engineering workflow.

Estimates project complexity based on:
  - number of features
  - domain
  - technology stack
  - integrations required
  - scale

Outputs:
  - complexity score (1-10)
  - estimated files
  - estimated APIs
  - estimated time
  - estimated team size
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ComplexityEstimate:
    """Complexity estimation for a project."""

    project_name: str
    complexity_score: float = 0.0
    estimated_files: int = 0
    estimated_apis: int = 0
    estimated_hours: float = 0.0
    estimated_team_size: int = 1
    confidence: float = 0.0
    breakdown: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "complexity_score": round(self.complexity_score, 1),
            "estimated_files": self.estimated_files,
            "estimated_apis": self.estimated_apis,
            "estimated_hours": round(self.estimated_hours, 1),
            "estimated_team_size": self.estimated_team_size,
            "confidence": round(self.confidence, 2),
            "breakdown": dict(self.breakdown),
        }


class ComplexityEstimator:
    """Estimate project complexity based on requirements.

    Uses heuristic rules and historical data.
    """

    # Base complexity by domain
    DOMAIN_BASE = {
        "hospital": 7.5,
        "ecommerce": 8.0,
        "finance": 9.0,
        "social": 8.5,
        "education": 6.5,
        "iot": 8.5,
        "ai": 9.5,
        "blockchain": 9.0,
        "general": 5.0,
    }

    # Feature complexity weights
    FEATURE_WEIGHTS = {
        "authentication": 1.5,
        "authorization": 1.3,
        "payment": 2.0,
        "real-time": 2.0,
        "file upload": 1.2,
        "notifications": 1.0,
        "search": 1.5,
        "reporting": 1.3,
        "analytics": 1.5,
        "ai": 2.5,
        "machine learning": 2.5,
        "blockchain": 2.0,
        "iot": 2.0,
        "mobile": 1.5,
        "api": 1.0,
        "admin": 0.8,
        "dashboard": 1.0,
    }

    # Technology complexity modifiers
    TECH_MODIFIERS = {
        "kubernetes": 1.5,
        "kafka": 1.3,
        "microservices": 1.8,
        "docker": 0.9,
        "postgresql": 0.8,
        "mongodb": 0.9,
        "redis": 0.7,
        "fastapi": 0.8,
        "django": 0.7,
        "react": 0.8,
        "vue": 0.7,
    }

    def estimate(self, requirement_analysis: Dict, architecture: Optional[Dict] = None) -> ComplexityEstimate:
        """Estimate project complexity."""
        project_name = requirement_analysis.get("project_name", "Unknown")
        domain = requirement_analysis.get("domain", "general")
        features = requirement_analysis.get("features", [])
        tech_stack = requirement_analysis.get("tech_stack", {})
        scale = requirement_analysis.get("scale", "startup")

        # Base complexity from domain
        base_complexity = self.DOMAIN_BASE.get(domain, 5.0)

        # Feature complexity
        feature_complexity = sum(
            self.FEATURE_WEIGHTS.get(feature.lower(), 1.0)
            for feature in features
        )

        # Technology modifiers
        tech_modifier = 1.0
        tech_breakdown = {}
        for category, tech in tech_stack.items():
            if isinstance(tech, str):
                tech_lower = tech.lower()
                if tech_lower in self.TECH_MODIFIERS:
                    tech_modifier *= self.TECH_MODIFIERS[tech_lower]
                    tech_breakdown[tech_lower] = self.TECH_MODIFIERS[tech_lower]

        # Scale modifier
        scale_modifier = {"startup": 0.9, "medium": 1.0, "enterprise": 1.3}.get(scale, 1.0)

        # Calculate final complexity
        raw_score = (base_complexity + feature_complexity * 0.5) * tech_modifier * scale_modifier
        complexity_score = min(10.0, max(1.0, raw_score))

        # Estimate files
        estimated_files = int(
            base_complexity * 10 +
            feature_complexity * 5 +
            (20 if scale == "enterprise" else 10 if scale == "medium" else 5)
        )

        # Estimate APIs
        estimated_apis = int(
            feature_complexity * 3 +
            (50 if scale == "enterprise" else 25 if scale == "medium" else 10)
        )

        # Estimate hours
        estimated_hours = estimated_files * 1.5 + estimated_apis * 0.5

        # Estimate team size
        if complexity_score >= 8.0:
            team_size = 4
        elif complexity_score >= 6.0:
            team_size = 3
        elif complexity_score >= 4.0:
            team_size = 2
        else:
            team_size = 1

        # Confidence based on data quality
        confidence = 0.7 if features else 0.5
        confidence += 0.1 if tech_stack else 0.0
        confidence = min(1.0, confidence)

        breakdown = {
            "base_complexity": round(base_complexity, 1),
            "feature_complexity": round(feature_complexity, 1),
            "tech_modifier": round(tech_modifier, 2),
            "scale_modifier": scale_modifier,
            "feature_count": len(features),
        }

        return ComplexityEstimate(
            project_name=project_name,
            complexity_score=complexity_score,
            estimated_files=estimated_files,
            estimated_apis=estimated_apis,
            estimated_hours=estimated_hours,
            estimated_team_size=team_size,
            confidence=confidence,
            breakdown=breakdown,
        )
