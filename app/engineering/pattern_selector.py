"""Design pattern selector for engineering workflow.

Automatically selects appropriate design patterns based on:
  - project type
  - domain
  - requirements
  - scale

Patterns:
  - Repository Pattern
  - Factory Pattern
  - Service Layer
  - MVC / MVVM
  - Clean Architecture
  - Hexagonal Architecture
  - CQRS
  - Event Sourcing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PatternSelection:
    """Selected design pattern with reasoning."""

    pattern: str = ""
    category: str = "general"
    reason: str = ""
    confidence: float = 0.0
    alternatives: List[str] = field(default_factory=list)
    applicable_components: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pattern": self.pattern,
            "category": self.category,
            "reason": self.reason,
            "confidence": round(self.confidence, 2),
            "alternatives": list(self.alternatives),
            "applicable_components": list(self.applicable_components),
        }


class PatternSelector:
    """Select appropriate design patterns for a project.

    Uses rule-based selection with project characteristics.
    """

    PATTERN_RULES = {
        "repository": {
            "triggers": ["database", "crud", "data access", "orm"],
            "reason": "Database-heavy project benefits from data access abstraction",
            "confidence": 0.9,
        },
        "factory": {
            "triggers": ["multiple types", "polymorphism", "creation"],
            "reason": "Multiple object types with shared interface",
            "confidence": 0.85,
        },
        "service_layer": {
            "triggers": ["business logic", "complex rules", "orchestration"],
            "reason": "Complex business logic needs separation from controllers",
            "confidence": 0.9,
        },
        "mvc": {
            "triggers": ["web", "dashboard", "admin", "portal"],
            "reason": "Standard web application structure",
            "confidence": 0.8,
        },
        "clean_architecture": {
            "triggers": ["enterprise", "large scale", "complex", "microservice"],
            "reason": "Large-scale project needs clear separation of concerns",
            "confidence": 0.85,
        },
        "hexagonal": {
            "triggers": ["testable", "isolated", "domain driven"],
            "reason": "High testability and external system isolation",
            "confidence": 0.8,
        },
        "cqrs": {
            "triggers": ["high traffic", "read write separation", "analytics"],
            "reason": "Different read and write workloads",
            "confidence": 0.75,
        },
        "event_sourcing": {
            "triggers": ["audit", "history", "event log", "time travel"],
            "reason": "Need to track all state changes",
            "confidence": 0.7,
        },
    }

    def select(self, requirement_analysis: Dict) -> List[PatternSelection]:
        """Select design patterns based on requirements."""
        selections = []
        features = requirement_analysis.get("features", [])
        domain = requirement_analysis.get("domain", "general")
        project_type = requirement_analysis.get("project_type", "web")
        scale = requirement_analysis.get("scale", "startup")
        keywords = requirement_analysis.get("keywords", [])

        # Build feature text for matching
        feature_text = " ".join(features + keywords + [domain, project_type, scale]).lower()

        for pattern_name, rule in self.PATTERN_RULES.items():
            matches = sum(1 for trigger in rule["triggers"] if trigger in feature_text)
            if matches > 0:
                confidence = min(1.0, rule["confidence"] + (matches * 0.05))
                alternatives = self._get_alternatives(pattern_name, feature_text)
                applicable = self._applicable_components(pattern_name, requirement_analysis)

                selections.append(PatternSelection(
                    pattern=pattern_name,
                    category=self._category(pattern_name),
                    reason=rule["reason"],
                    confidence=confidence,
                    alternatives=alternatives,
                    applicable_components=applicable,
                ))

        # Sort by confidence
        selections.sort(key=lambda s: s.confidence, reverse=True)
        return selections

    def _category(self, pattern: str) -> str:
        categories = {
            "repository": "data_access",
            "factory": "creational",
            "service_layer": "architecture",
            "mvc": "architecture",
            "clean_architecture": "architecture",
            "hexagonal": "architecture",
            "cqrs": "data",
            "event_sourcing": "data",
        }
        return categories.get(pattern, "general")

    def _get_alternatives(self, selected: str, feature_text: str) -> List[str]:
        """Get alternative patterns that might also apply."""
        alternatives = []
        for pattern_name, rule in self.PATTERN_RULES.items():
            if pattern_name == selected:
                continue
            matches = sum(1 for trigger in rule["triggers"] if trigger in feature_text)
            if matches > 0:
                alternatives.append(pattern_name)
        return alternatives[:3]

    def _applicable_components(self, pattern: str, analysis: Dict) -> List[str]:
        """Determine which components this pattern applies to."""
        components = []
        modules = analysis.get("modules", [])

        if pattern == "repository":
            components = modules if modules else ["data_access", "models"]
        elif pattern == "service_layer":
            components = modules if modules else ["business_logic", "controllers"]
        elif pattern == "factory":
            components = ["factories", "builders"]
        elif pattern in ["mvc", "clean_architecture", "hexagonal"]:
            components = ["controllers", "services", "models", "views"]
        elif pattern == "cqrs":
            components = ["read_model", "write_model", "api"]
        elif pattern == "event_sourcing":
            components = ["event_store", "projections", "aggregates"]

        return components
