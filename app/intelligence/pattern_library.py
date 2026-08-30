"""Pattern Library for Jarvis-X.

Stores reusable engineering patterns that can be applied across projects:
  - JWT Authentication
  - REST CRUD
  - Repository Pattern
  - Service Layer
  - Pagination
  - Caching
  - Docker configuration
  - CI/CD pipelines

Instead of generating these from scratch every time, Jarvis reuses them.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EngineeringPattern:
    """Single reusable engineering pattern."""

    pattern_id: str = ""
    name: str = ""
    category: str = "general"  # auth, database, api, frontend, devops, testing
    description: str = ""
    code_template: str = ""
    language: str = "python"
    framework: str = ""
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.pattern_id:
            self.pattern_id = f"pat-{hashlib.sha256((self.name + self.category).encode()).hexdigest()[:12]}"

    def to_dict(self) -> dict:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "code_template": self.code_template,
            "language": self.language,
            "framework": self.framework,
            "tags": list(self.tags),
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }


class PatternLibrary:
    """Storage and retrieval for reusable engineering patterns."""

    def __init__(self, patterns_path: str = "data/pattern_library.json"):
        self.patterns_path = patterns_path
        self._patterns: Dict[str, EngineeringPattern] = {}
        os.makedirs(os.path.dirname(patterns_path) or ".", exist_ok=True)
        self._load()
        self._seed_defaults()

    def _load(self):
        if not os.path.exists(self.patterns_path):
            return
        try:
            with open(self.patterns_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict) and item.get("pattern_id"):
                        pattern = EngineeringPattern(**item)
                        self._patterns[pattern.pattern_id] = pattern
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self):
        try:
            with open(self.patterns_path, "w", encoding="utf-8") as f:
                json.dump([p.to_dict() for p in self._patterns.values()], f, indent=2, default=str)
        except OSError:
            pass

    def _seed_defaults(self):
        """Seed with common engineering patterns if none exist."""
        if self._patterns:
            return
        defaults = [
            EngineeringPattern(
                name="JWT Authentication",
                category="auth",
                description="JSON Web Token authentication with refresh tokens",
                code_template="# JWT auth pattern\nimport jwt\nfrom datetime import datetime, timedelta\n\ndef create_token(user_id):\n    payload = {\n        'user_id': user_id,\n        'exp': datetime.utcnow() + timedelta(hours=1)\n    }\n    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')",
                language="python",
                framework="fastapi",
                tags=["auth", "jwt", "security", "api"],
            ),
            EngineeringPattern(
                name="Repository Pattern",
                category="database",
                description="Data access abstraction layer",
                code_template="# Repository pattern\nclass UserRepository:\n    def __init__(self, db):\n        self.db = db\n    \n    def find_by_id(self, user_id):\n        return self.db.query(User).filter(User.id == user_id).first()\n    \n    def create(self, data):\n        user = User(**data)\n        self.db.add(user)\n        self.db.commit()\n        return user",
                language="python",
                framework="sqlalchemy",
                tags=["database", "repository", "pattern", "dao"],
            ),
            EngineeringPattern(
                name="REST CRUD",
                category="api",
                description="Standard REST CRUD endpoints",
                code_template="# REST CRUD pattern\n@app.get('/items')\ndef list_items():\n    return db.query(Item).all()\n\n@app.post('/items')\ndef create_item(item: ItemSchema):\n    db_item = Item(**item.dict())\n    db.add(db_item)\n    db.commit()\n    return db_item\n\n@app.get('/items/{item_id}')\ndef get_item(item_id: int):\n    return db.query(Item).filter(Item.id == item_id).first()\n\n@app.put('/items/{item_id}')\ndef update_item(item_id: int, item: ItemSchema):\n    db_item = db.query(Item).filter(Item.id == item_id).first()\n    for key, value in item.dict().items():\n        setattr(db_item, key, value)\n    db.commit()\n    return db_item\n\n@app.delete('/items/{item_id}')\ndef delete_item(item_id: int):\n    db_item = db.query(Item).filter(Item.id == item_id).first()\n    db.delete(db_item)\n    db.commit()\n    return {'deleted': True}",
                language="python",
                framework="fastapi",
                tags=["api", "rest", "crud", "http"],
            ),
            EngineeringPattern(
                name="Docker Compose",
                category="devops",
                description="Multi-service Docker Compose configuration",
                code_template="version: '3.8'\nservices:\n  api:\n    build: .\n    ports:\n      - '8000:8000'\n    environment:\n      - DATABASE_URL=postgresql://user:pass@db:5432/app\n    depends_on:\n      - db\n  db:\n    image: postgres:15\n    environment:\n      - POSTGRES_USER=user\n      - POSTGRES_PASSWORD=pass\n      - POSTGRES_DB=app\n    volumes:\n      - pgdata:/var/lib/postgresql/data\nvolumes:\n  pgdata:",
                language="yaml",
                framework="docker",
                tags=["docker", "compose", "devops", "deployment"],
            ),
        ]
        for pattern in defaults:
            self._patterns[pattern.pattern_id] = pattern
        self._save()

    def add_pattern(self, pattern: EngineeringPattern) -> str:
        """Add a new pattern to the library."""
        self._patterns[pattern.pattern_id] = pattern
        self._save()
        return pattern.pattern_id

    def get_pattern(self, pattern_id: str) -> Optional[EngineeringPattern]:
        """Get a pattern by ID."""
        return self._patterns.get(pattern_id)

    def find_patterns(self, category: Optional[str] = None, tags: Optional[List[str]] = None,
                      language: Optional[str] = None, limit: int = 10) -> List[EngineeringPattern]:
        """Find patterns matching criteria."""
        results = list(self._patterns.values())
        if category:
            results = [p for p in results if p.category == category]
        if language:
            results = [p for p in results if p.language == language]
        if tags:
            results = [p for p in results if any(tag in p.tags for tag in tags)]
        results.sort(key=lambda p: (p.success_rate, p.usage_count), reverse=True)
        return results[:max(1, limit)]

    def record_usage(self, pattern_id: str, success: bool):
        """Record usage of a pattern."""
        pattern = self._patterns.get(pattern_id)
        if pattern:
            pattern.usage_count += 1
            if success:
                total_success = pattern.success_rate * (pattern.usage_count - 1) + 1
                pattern.success_rate = total_success / pattern.usage_count
            else:
                total_success = pattern.success_rate * (pattern.usage_count - 1)
                pattern.success_rate = total_success / pattern.usage_count
            pattern.updated_at = datetime.now(timezone.utc).isoformat()
            self._save()

    def stats(self) -> Dict[str, Any]:
        categories: Dict[str, int] = {}
        for p in self._patterns.values():
            categories[p.category] = categories.get(p.category, 0) + 1
        return {
            "total_patterns": len(self._patterns),
            "categories": categories,
            "total_usages": sum(p.usage_count for p in self._patterns.values()),
        }
