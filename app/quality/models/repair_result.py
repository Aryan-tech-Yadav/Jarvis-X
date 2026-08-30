"""Repair result and root cause analysis models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .test_result import TestSuiteResult


@dataclass
class RootCauseAnalysis:
    failure: str
    root_cause: str
    confidence: float = 0.95  # 0.0 to 1.0
    repair_strategy: str = ""
    target_files: List[str] = field(default_factory=list)
    error_category: str = "runtime"  # syntax, import, config, attribute, type, assertion, performance, security
    suggested_patch: str = ""
    raw_traceback: str = ""
    failing_symbol: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure": self.failure,
            "root_cause": self.root_cause,
            "confidence": round(float(self.confidence), 4),
            "repair_strategy": self.repair_strategy,
            "target_files": list(self.target_files),
            "error_category": self.error_category,
            "suggested_patch": self.suggested_patch,
            "raw_traceback": self.raw_traceback,
            "failing_symbol": self.failing_symbol,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RootCauseAnalysis:
        return cls(
            failure=data.get("failure", "Unknown Failure"),
            root_cause=data.get("root_cause", "Unknown Root Cause"),
            confidence=float(data.get("confidence", 0.5)),
            repair_strategy=data.get("repair_strategy", ""),
            target_files=list(data.get("target_files", [])),
            error_category=data.get("error_category", "runtime"),
            suggested_patch=data.get("suggested_patch", ""),
            raw_traceback=data.get("raw_traceback", ""),
            failing_symbol=data.get("failing_symbol", ""),
        )


@dataclass
class Patch:
    file_path: str
    original_content: str
    modified_content: str
    diff: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "original_content": self.original_content,
            "modified_content": self.modified_content,
            "diff": self.diff,
            "description": self.description,
        }


@dataclass
class RepairAttempt:
    repair_id: str = field(default_factory=lambda: str(uuid4()))
    root_cause: Optional[RootCauseAnalysis] = None
    strategy_used: str = ""
    patches: List[Patch] = field(default_factory=list)
    success: bool = False
    retest_result: Optional[TestSuiteResult] = None
    confidence_score: float = 0.0
    repair_time_sec: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repair_id": self.repair_id,
            "root_cause": self.root_cause.to_dict() if self.root_cause else None,
            "strategy_used": self.strategy_used,
            "patches": [p.to_dict() for p in self.patches],
            "success": self.success,
            "retest_result": self.retest_result.to_dict() if self.retest_result else None,
            "confidence_score": round(float(self.confidence_score), 4),
            "repair_time_sec": round(float(self.repair_time_sec), 4),
            "timestamp": self.timestamp,
            "error_message": self.error_message,
        }


@dataclass
class SelfHealingResult:
    original_failed: bool = True
    root_cause: Optional[RootCauseAnalysis] = None
    repairs_attempted: List[RepairAttempt] = field(default_factory=list)
    final_success: bool = False
    final_test_result: Optional[TestSuiteResult] = None
    total_repair_time_sec: float = 0.0
    knowledge_saved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_failed": self.original_failed,
            "root_cause": self.root_cause.to_dict() if self.root_cause else None,
            "repairs_attempted": [r.to_dict() for r in self.repairs_attempted],
            "final_success": self.final_success,
            "final_test_result": self.final_test_result.to_dict() if self.final_test_result else None,
            "total_repair_time_sec": round(float(self.total_repair_time_sec), 4),
            "knowledge_saved": self.knowledge_saved,
        }
