"""Autonomous Success Pattern Library for architectural and code reuse."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models.pattern import Pattern, PatternType


class SuccessPatternEngine:
    """Stores high-performing architectures and blueprints to continuously reuse proven solutions."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir else (Path.cwd() / "knowledge")
        self.patterns_dir = self.knowledge_dir / "patterns"
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.patterns_dir / "pattern_store.json"
        self._patterns: List[Pattern] = self._load()
        if not self._patterns:
            self._seed_default_patterns()

    def _load(self) -> List[Pattern]:
        if not self.store_file.exists():
            return []
        try:
            data = json.loads(self.store_file.read_text(encoding="utf-8"))
            records = []
            for item in data:
                pt = item.get("pattern_type", "architecture")
                try:
                    pattern_type = PatternType(pt)
                except ValueError:
                    pattern_type = PatternType.ARCHITECTURE
                item_copy = dict(item)
                item_copy["pattern_type"] = pattern_type
                records.append(Pattern(**item_copy))
            return records
        except Exception:
            return []

    def _save(self):
        try:
            payload = [p.to_dict() for p in self._patterns]
            self.store_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _seed_default_patterns(self):
        defaults = [
            Pattern(
                name="FastAPI + PostgreSQL + Redis ERP Architecture",
                pattern_type=PatternType.ARCHITECTURE,
                domain="erp",
                description="High-throughput modular ERP architecture with transactional isolation, Redis caching, and async endpoints.",
                blueprint={
                    "framework": "fastapi",
                    "database": "postgresql",
                    "cache": "redis",
                    "layers": ["api", "services", "repositories", "models", "schemas"],
                },
                benchmark_score=97.0,
                recommended=True,
                tags=["erp", "enterprise", "fastapi", "postgres"],
            ),
            Pattern(
                name="Clean Architecture CRM Pipeline",
                pattern_type=PatternType.ARCHITECTURE,
                domain="crm",
                description="Event-driven CRM architecture with customer lifecycle management and webhook integration.",
                blueprint={
                    "framework": "fastapi",
                    "database": "postgresql",
                    "message_bus": "event_emitter",
                    "layers": ["routes", "domain", "infra"],
                },
                benchmark_score=96.5,
                recommended=True,
                tags=["crm", "sales", "fastapi"],
            ),
            Pattern(
                name="Resilient JWT Auth Flow with Refresh Tokens",
                pattern_type=PatternType.CODE,
                domain="security",
                description="Zero-trust JWT authentication service with token rotation, revocation blacklist, and bcrypt password hashing.",
                blueprint={
                    "algorithm": "HS256",
                    "access_token_ttl_min": 15,
                    "refresh_token_ttl_days": 7,
                },
                benchmark_score=98.0,
                recommended=True,
                tags=["auth", "jwt", "security"],
            ),
        ]
        self._patterns.extend(defaults)
        self._save()

    def register_pattern(
        self,
        name: str,
        pattern_type: PatternType,
        domain: str,
        blueprint: Dict[str, Any],
        benchmark_score: float = 90.0,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Pattern:
        pattern = Pattern(
            name=name,
            pattern_type=pattern_type,
            domain=domain,
            blueprint=blueprint,
            benchmark_score=benchmark_score,
            description=description,
            tags=tags or [],
            recommended=(benchmark_score >= 90.0),
        )
        self._patterns.append(pattern)
        self._save()
        return pattern

    def find_recommended_architecture(self, domain: str, requirements: Optional[str] = None) -> Optional[Pattern]:
        candidates = [p for p in self._patterns if p.pattern_type == PatternType.ARCHITECTURE and p.recommended]
        # Match domain first
        domain_matches = [p for p in candidates if p.domain.lower() == domain.lower()]
        if domain_matches:
            return max(domain_matches, key=lambda x: x.benchmark_score)
        if candidates:
            return max(candidates, key=lambda x: x.benchmark_score)
        return None

    def record_pattern_usage(self, pattern_id: str, success: bool, benchmark_score: float) -> Optional[Pattern]:
        for p in self._patterns:
            if p.pattern_id == pattern_id:
                p.times_used += 1
                current_rate = p.success_rate
                new_rate = (current_rate * (p.times_used - 1) + (1.0 if success else 0.0)) / p.times_used
                p.success_rate = round(new_rate, 4)
                p.benchmark_score = round((p.benchmark_score + benchmark_score) / 2.0, 2)
                p.recommended = (p.success_rate >= 0.85 and p.benchmark_score >= 90.0)
                self._save()
                return p
        return None

    def list_patterns(self, pattern_type: Optional[PatternType] = None) -> List[Pattern]:
        if pattern_type:
            return [p for p in self._patterns if p.pattern_type == pattern_type]
        return list(self._patterns)
