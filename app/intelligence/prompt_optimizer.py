"""Prompt Optimizer for Jarvis-X.

Automatically optimizes prompts based on execution outcomes.

Flow:
  1. Run agent with prompt v1 → score 92
  2. Run agent with prompt v2 → score 95
  3. Keep v2 for future use

Tracks:
  - Prompt versions
  - Associated scores
  - Success rates
  - Auto-selects best performing prompts
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class PromptVersion:
    """Single prompt version record."""

    prompt_id: str = ""
    agent_name: str = ""
    prompt_text: str = ""
    version: int = 1
    score: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    is_active: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.prompt_id:
            self.prompt_id = f"prompt-{hashlib.sha256(self.prompt_text.encode()).hexdigest()[:12]}"

    def to_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "agent_name": self.agent_name,
            "prompt_text": self.prompt_text,
            "version": self.version,
            "score": self.score,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class PromptOptimizer:
    """Track and optimize agent prompts based on outcomes."""

    def __init__(self, prompts_path: str = "data/prompt_versions.json"):
        self.prompts_path = prompts_path
        self._versions: Dict[str, List[PromptVersion]] = {}  # agent_name -> [versions]
        os.makedirs(os.path.dirname(prompts_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self.prompts_path):
            return
        try:
            with open(self.prompts_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        pv = PromptVersion(**item)
                        agent = pv.agent_name
                        if agent not in self._versions:
                            self._versions[agent] = []
                        self._versions[agent].append(pv)
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self):
        all_versions = []
        for versions in self._versions.values():
            all_versions.extend(versions)
        try:
            with open(self.prompts_path, "w", encoding="utf-8") as f:
                json.dump([v.to_dict() for v in all_versions], f, indent=2, default=str)
        except OSError:
            pass

    def record_prompt(self, agent_name: str, prompt_text: str, score: float,
                      success: bool = True) -> PromptVersion:
        """Record a prompt execution and its score."""
        prompt_id = f"prompt-{hashlib.sha256(prompt_text.encode()).hexdigest()[:12]}"
        existing = self._versions.get(agent_name, [])
        version = len([v for v in existing if v.agent_name == agent_name]) + 1

        pv = PromptVersion(
            prompt_id=prompt_id,
            agent_name=agent_name,
            prompt_text=prompt_text,
            version=version,
            score=score,
            success_count=1 if success else 0,
            failure_count=0 if success else 1,
            is_active=False,
        )

        # Update existing if same prompt_id
        for existing_pv in existing:
            if existing_pv.prompt_id == prompt_id:
                existing_pv.score = (existing_pv.score * existing_pv.success_count + score) / max(1, existing_pv.success_count + existing_pv.failure_count)
                existing_pv.success_count += 1 if success else 0
                existing_pv.failure_count += 0 if success else 1
                self._save()
                return existing_pv

        if agent_name not in self._versions:
            self._versions[agent_name] = []
        self._versions[agent_name].append(pv)
        self._save()
        return pv

    def get_best_prompt(self, agent_name: str) -> Optional[PromptVersion]:
        """Get the best performing prompt for an agent."""
        versions = self._versions.get(agent_name, [])
        if not versions:
            return None
        return max(versions, key=lambda v: v.score)

    def get_active_prompt(self, agent_name: str) -> Optional[PromptVersion]:
        """Get the currently active prompt for an agent."""
        versions = self._versions.get(agent_name, [])
        active = [v for v in versions if v.is_active]
        if active:
            return active[-1]
        if versions:
            best = max(versions, key=lambda v: v.score)
            best.is_active = True
            self._save()
            return best
        return None

    def promote_to_active(self, agent_name: str, prompt_id: str) -> bool:
        """Promote a prompt version to active."""
        versions = self._versions.get(agent_name, [])
        for pv in versions:
            pv.is_active = (pv.prompt_id == prompt_id)
        self._save()
        return True

    def stats(self) -> Dict[str, Any]:
        total_prompts = sum(len(v) for v in self._versions.values())
        return {
            "total_agents": len(self._versions),
            "total_prompts": total_prompts,
            "agents": {agent: len(versions) for agent, versions in self._versions.items()},
        }
