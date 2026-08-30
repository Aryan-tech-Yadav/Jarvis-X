"""Decision Recorder for capturing explainable AI decisions with evidence and alternatives."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class DecisionEntry:
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    decision: str = ""
    reason: str = ""
    alternatives: List[str] = field(default_factory=list)
    confidence: float = 0.95
    evidence: str = ""
    stage: str = "planning"
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision": self.decision,
            "reason": self.reason,
            "alternatives": list(self.alternatives),
            "confidence": round(float(self.confidence), 4),
            "evidence": self.evidence,
            "stage": self.stage,
            "context": dict(self.context),
            "timestamp": self.timestamp,
        }


class DecisionRecorder:
    """Records and queries transparent, audit-ready AI decisions."""

    def __init__(self, store_dir: Optional[str] = None):
        self.store_dir = Path(store_dir).resolve() if store_dir else (Path.cwd() / "knowledge" / "decisions")
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._entries: List[DecisionEntry] = []

    def record_decision(
        self,
        decision: str,
        reason: str,
        alternatives: Optional[List[str]] = None,
        confidence: float = 0.95,
        evidence: str = "",
        stage: str = "planning",
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionEntry:
        entry = DecisionEntry(
            decision=decision,
            reason=reason,
            alternatives=alternatives or [],
            confidence=confidence,
            evidence=evidence,
            stage=stage,
            context=context or {},
        )
        self._entries.append(entry)
        self._persist_entry(entry)
        return entry

    def _persist_entry(self, entry: DecisionEntry):
        try:
            f = self.store_dir / f"decision_{entry.decision_id[:8]}.json"
            f.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")
        except Exception:
            pass

    def query_decisions(self, stage: Optional[str] = None) -> List[DecisionEntry]:
        if stage:
            return [e for e in self._entries if e.stage.lower() == stage.lower()]
        return list(self._entries)

    def to_dict(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries]
