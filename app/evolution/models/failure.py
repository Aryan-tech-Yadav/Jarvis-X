"""Failure tracking and historical root cause models for self-improvement."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class FailureCategory(str, Enum):
    CONFIGURATION = "configuration"
    IMPORT = "import"
    SYNTAX = "syntax"
    ATTRIBUTE = "attribute"
    TYPE = "type"
    ASSERTION = "assertion"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    SECURITY = "security"
    GENERAL = "general"


@dataclass
class FailureRecord:
    failure_id: str = field(default_factory=lambda: str(uuid4()))
    problem: str = ""
    category: FailureCategory = FailureCategory.GENERAL
    reason: str = ""
    root_cause: str = ""
    fix_strategy: str = ""
    code_diff: str = ""
    success: bool = True
    repair_time_sec: float = 0.0
    occurrences: int = 1
    domain: str = "general"
    failing_symbol: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "problem": self.problem,
            "category": self.category.value if isinstance(self.category, FailureCategory) else str(self.category),
            "reason": self.reason,
            "root_cause": self.root_cause,
            "fix_strategy": self.fix_strategy,
            "code_diff": self.code_diff,
            "success": self.success,
            "repair_time_sec": round(float(self.repair_time_sec), 3),
            "occurrences": self.occurrences,
            "domain": self.domain,
            "failing_symbol": self.failing_symbol,
            "created_at": self.created_at,
        }
