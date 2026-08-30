"""Autonomous Failure Database for recording problems, reasons, and proven fixes."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models.failure import FailureCategory, FailureRecord


class FailureEngine:
    """Historical Failure Database: enables instant, proven recall for recurring engineering problems."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir else (Path.cwd() / "knowledge")
        self.failures_dir = self.knowledge_dir / "failures"
        self.failures_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.failures_dir / "failure_store.json"
        self._failures: List[FailureRecord] = self._load()

    def _load(self) -> List[FailureRecord]:
        if not self.store_file.exists():
            return []
        try:
            data = json.loads(self.store_file.read_text(encoding="utf-8"))
            records = []
            for item in data:
                cat = item.get("category", "general")
                try:
                    category = FailureCategory(cat)
                except ValueError:
                    category = FailureCategory.GENERAL
                item_copy = dict(item)
                item_copy["category"] = category
                records.append(FailureRecord(**item_copy))
            return records
        except Exception:
            return []

    def _save(self):
        try:
            payload = [f.to_dict() for f in self._failures]
            self.store_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def record_failure(
        self,
        problem: str,
        reason: str,
        root_cause: str,
        fix_strategy: str,
        code_diff: str = "",
        success: bool = True,
        repair_time_sec: float = 0.0,
        category: FailureCategory = FailureCategory.GENERAL,
        domain: str = "general",
        failing_symbol: str = "",
    ) -> FailureRecord:
        # Check if identical failure exists, increment occurrences
        for rec in self._failures:
            if rec.problem.lower() == problem.lower() and rec.category == category:
                rec.occurrences += 1
                rec.fix_strategy = fix_strategy
                rec.success = success
                rec.code_diff = code_diff or rec.code_diff
                rec.repair_time_sec = repair_time_sec
                self._save()
                return rec

        record = FailureRecord(
            problem=problem,
            category=category,
            reason=reason,
            root_cause=root_cause,
            fix_strategy=fix_strategy,
            code_diff=code_diff,
            success=success,
            repair_time_sec=repair_time_sec,
            domain=domain,
            failing_symbol=failing_symbol,
        )
        self._failures.append(record)
        self._save()
        return record

    def find_direct_solution(
        self,
        problem: str,
        category: Optional[FailureCategory] = None,
        failing_symbol: str = "",
    ) -> Optional[FailureRecord]:
        # 1. Exact symbol match
        if failing_symbol:
            for f in reversed(self._failures):
                if f.success and f.failing_symbol == failing_symbol:
                    return f

        # 2. Problem substring match
        for f in reversed(self._failures):
            if f.success:
                if (problem.lower() in f.problem.lower()) or (f.problem.lower() in problem.lower()):
                    return f

        # 3. Category match
        if category:
            for f in reversed(self._failures):
                if f.success and f.category == category:
                    return f

        return None

    def get_most_common_failures(self, limit: int = 5) -> List[Dict[str, Any]]:
        sorted_failures = sorted(self._failures, key=lambda x: x.occurrences, reverse=True)
        return [f.to_dict() for f in sorted_failures[:limit]]
