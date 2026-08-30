"""Machine-readable report for one multi-agent execution."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ExecutionReport:
    task: str
    run_id: str = field(default_factory=lambda: f"run_{uuid.uuid4().hex[:10]}")
    agents: Dict[str, str] = field(default_factory=dict)
    runtime_seconds: float = 0.0
    score: Optional[float] = None
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def record(self, agent: str, success: bool) -> None:
        self.agents[agent] = "success" if success else "failed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, directory: str = "reports") -> Path:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{self.run_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path
