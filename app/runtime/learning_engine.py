"""Learning Engine - Generate learnings from reflections.

Converts reflection insights into actionable learnings:
  - Best practices
  - Common mistakes to avoid
  - Tool usage patterns
  - Quality improvements
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class Learning:
    """A single learning entry."""
    learning_id: str
    category: str
    description: str
    confidence: float = 1.0
    source: str = ""
    created_at: str = ""
    usage_count: int = 0
    success_count: int = 0


class LearningEngine:
    """Generate and manage learnings from reflections.

    Learning categories:
      - best_practice: Things that work well
      - mistake: Common mistakes to avoid
      - tool_usage: How to use tools effectively
      - quality: Code quality improvements
      - performance: Performance optimizations
    """

    def __init__(self, knowledge_dir: str = "data/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._learnings: Dict[str, Learning] = {}
        self._load_learnings()

    def generate_from_reflection(self, reflection: Dict[str, Any]) -> List[Learning]:
        """Generate learnings from reflection.

        Args:
            reflection: Reflection result dictionary

        Returns:
            List of generated learnings
        """
        learnings = []

        # Generate from mistakes
        for mistake in reflection.get("mistakes", []):
            learning = self._create_learning(
                category="mistake",
                description=f"Avoid: {mistake}",
                source="reflection",
            )
            learnings.append(learning)

        # Generate from suggestions
        for suggestion in reflection.get("suggestions", []):
            learning = self._create_learning(
                category="best_practice",
                description=f"Practice: {suggestion}",
                source="reflection",
            )
            learnings.append(learning)

        # Generate from failure reasons
        for reason in reflection.get("failure_reasons", []):
            learning = self._create_learning(
                category="mistake",
                description=f"Watch out: {reason}",
                source="reflection",
                confidence=0.8,
            )
            learnings.append(learning)

        # Save learnings
        for learning in learnings:
            self._save_learning(learning)

        return learnings

    def _create_learning(self, category: str, description: str, source: str, confidence: float = 1.0) -> Learning:
        """Create a new learning entry.

        Args:
            category: Learning category
            description: Learning description
            source: Source of learning
            confidence: Confidence score

        Returns:
            Learning entry
        """
        learning_id = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(description) % 10000}"
        return Learning(
            learning_id=learning_id,
            category=category,
            description=description,
            confidence=confidence,
            source=source,
            created_at=datetime.now().isoformat(),
        )

    def _save_learning(self, learning: Learning):
        """Save learning to disk.

        Args:
            learning: Learning entry
        """
        self._learnings[learning.learning_id] = learning
        try:
            filename = (
                "best_practices.json"
                if learning.category == "best_practice"
                else f"{learning.category}.json"
            )
            filepath = self.knowledge_dir / filename
            data = self._load_json(filepath)
            data[learning.learning_id] = {
                "learning_id": learning.learning_id,
                "category": learning.category,
                "description": learning.description,
                "confidence": learning.confidence,
                "source": learning.source,
                "created_at": learning.created_at,
                "usage_count": learning.usage_count,
                "success_count": learning.success_count,
            }
            self._save_json(filepath, data)
        except Exception as exc:
            Logger.warning(f"[Learning] Save failed: {exc}")

    def get_learnings(self, category: str = "") -> List[Learning]:
        """Get all learnings, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of learnings
        """
        learnings = list(self._learnings.values())
        if category:
            learnings = [l for l in learnings if l.category == category]
        return sorted(learnings, key=lambda l: l.confidence, reverse=True)

    def get_best_practices(self) -> List[str]:
        """Get list of best practices.

        Returns:
            List of best practice descriptions
        """
        return [l.description for l in self.get_learnings("best_practice")]

    def get_common_mistakes(self) -> List[str]:
        """Get list of common mistakes to avoid.

        Returns:
            List of mistake descriptions
        """
        return [l.description for l in self.get_learnings("mistake")]

    def record_usage(self, learning_id: str, success: bool):
        """Record usage of a learning.

        Args:
            learning_id: Learning ID
            success: Whether it was successful
        """
        learning = self._learnings.get(learning_id)
        if learning:
            learning.usage_count += 1
            if success:
                learning.success_count += 1
            self._save_learning(learning)

    def _load_learnings(self):
        """Load learnings from disk."""
        for filepath in self.knowledge_dir.glob("*.json"):
            try:
                data = self._load_json(filepath)
                for learning_id, entry in data.items():
                    learning = Learning(
                        learning_id=entry["learning_id"],
                        category=entry["category"],
                        description=entry["description"],
                        confidence=entry.get("confidence", 1.0),
                        source=entry.get("source", ""),
                        created_at=entry.get("created_at", ""),
                        usage_count=entry.get("usage_count", 0),
                        success_count=entry.get("success_count", 0),
                    )
                    self._learnings[learning.learning_id] = learning
            except Exception:
                pass

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_json(self, path: Path, data: Dict[str, Any]):
        """Save JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
