"""Evolution database for tracking self-improvement history.

Stores evolution records, versions, scores, and metadata.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EvolutionRecord:
    """Single evolution record."""

    evolution_id: str
    plan: Dict[str, Any] = field(default_factory=dict)
    baseline: Dict[str, Any] = field(default_factory=dict)
    final: Dict[str, Any] = field(default_factory=dict)
    applied: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0
    status: str = "completed"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evolution_id": self.evolution_id,
            "plan": dict(self.plan),
            "baseline": dict(self.baseline),
            "final": dict(self.final),
            "applied": list(self.applied),
            "rejected": list(self.rejected),
            "duration": round(self.duration, 3),
            "status": self.status,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class EvolutionDB:
    """Persist and retrieve evolution history."""

    def __init__(self, db_path: str = "data/evolution.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def close(self):
        """Close database connection."""
        # SQLite connections are closed via context managers,
        # but we expose this for explicit cleanup in tests.
        pass

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evolutions (
                    evolution_id TEXT PRIMARY KEY,
                    plan TEXT,
                    baseline TEXT,
                    final TEXT,
                    applied TEXT,
                    rejected TEXT,
                    duration REAL,
                    status TEXT,
                    created_at TEXT,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    version_id TEXT PRIMARY KEY,
                    evolution_id TEXT,
                    version_name TEXT,
                    score REAL,
                    timestamp TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()

    def record_evolution(self, plan: Dict[str, Any], baseline: Dict[str, Any], 
                        applied: List[Dict[str, Any]], rejected: List[Dict[str, Any]],
                        duration: float, status: str = "completed",
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record a new evolution."""
        evolution_id = f"evo-{uuid.uuid4().hex[:12]}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO evolutions 
                   (evolution_id, plan, baseline, final, applied, rejected, duration, status, created_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evolution_id,
                    json.dumps(plan, default=str),
                    json.dumps(baseline, default=str),
                    json.dumps({}, default=str),
                    json.dumps(applied, default=str),
                    json.dumps(rejected, default=str),
                    duration,
                    status,
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(metadata or {}, default=str),
                )
            )
            conn.commit()
        
        return evolution_id

    def record_version(self, evolution_id: str, version_name: str, score: float,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record a version snapshot."""
        version_id = f"ver-{uuid.uuid4().hex[:12]}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO versions 
                   (version_id, evolution_id, version_name, score, timestamp, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    version_id,
                    evolution_id,
                    version_name,
                    score,
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(metadata or {}, default=str),
                )
            )
            conn.commit()
        
        return version_id

    def get_evolution(self, evolution_id: str) -> Optional[EvolutionRecord]:
        """Get evolution by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM evolutions WHERE evolution_id = ?", (evolution_id,))
            row = cursor.fetchone()
            if row:
                return EvolutionRecord(
                    evolution_id=row["evolution_id"],
                    plan=json.loads(row["plan"] or "{}"),
                    baseline=json.loads(row["baseline"] or "{}"),
                    final=json.loads(row["final"] or "{}"),
                    applied=json.loads(row["applied"] or "[]"),
                    rejected=json.loads(row["rejected"] or "[]"),
                    duration=row["duration"],
                    status=row["status"],
                    created_at=row["created_at"],
                    metadata=json.loads(row["metadata"] or "{}"),
                )
        return None

    def get_versions(self, evolution_id: str) -> List[Dict[str, Any]]:
        """Get all versions for an evolution."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM versions WHERE evolution_id = ? ORDER BY timestamp",
                (evolution_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_evolutions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent evolution records."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM evolutions ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Get evolution statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM evolutions")
            total = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM evolutions WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT AVG(duration) FROM evolutions")
            avg_duration = cursor.fetchone()[0] or 0.0
            
            cursor = conn.execute("SELECT SUM(json_array_length(applied)) FROM evolutions")
            total_applied = cursor.fetchone()[0] or 0
        
        return {
            "total_evolutions": total,
            "completed": completed,
            "failed": total - completed,
            "avg_duration": round(avg_duration, 3),
            "total_improvements_applied": total_applied,
        }
