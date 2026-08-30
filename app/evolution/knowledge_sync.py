"""Knowledge Synchronization Engine across Architecture, Security, Performance, Repairs, and Lessons."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models.knowledge import KnowledgeCategory, KnowledgeEntry


class KnowledgeSync:
    """Manages persistent categorized knowledge across all engineering domains."""

    CATEGORIES = [
        KnowledgeCategory.ARCHITECTURE,
        KnowledgeCategory.SECURITY,
        KnowledgeCategory.PERFORMANCE,
        KnowledgeCategory.REPAIRS,
        KnowledgeCategory.BENCHMARKS,
        KnowledgeCategory.PATTERNS,
        KnowledgeCategory.PROMPTS,
        KnowledgeCategory.LESSONS,
    ]

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir else (Path.cwd() / "knowledge")
        self._ensure_directories()

    def _ensure_directories(self):
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        for cat in self.CATEGORIES:
            cat_dir = self.knowledge_dir / cat.value
            cat_dir.mkdir(parents=True, exist_ok=True)

    def sync_entry(
        self,
        category: KnowledgeCategory,
        title: str,
        summary: str,
        content: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        source_project: str = "",
        confidence: float = 0.95,
    ) -> KnowledgeEntry:
        self._ensure_directories()
        cat_dir = self.knowledge_dir / (category.value if isinstance(category, KnowledgeCategory) else str(category))
        cat_dir.mkdir(parents=True, exist_ok=True)

        entry = KnowledgeEntry(
            category=category,
            title=title,
            summary=summary,
            content=content or {},
            tags=tags or [],
            source_project=source_project,
            confidence=confidence,
        )

        safe_title = "".join(c if c.isalnum() else "_" for c in title[:30]).strip("_").lower()
        file_path = cat_dir / f"{safe_title}_{entry.entry_id[:8]}.json"
        try:
            file_path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")
        except Exception:
            pass

        return entry

    def query_knowledge(
        self,
        category: Optional[KnowledgeCategory] = None,
        tag: Optional[str] = None,
        query_text: Optional[str] = None,
        limit: int = 10,
    ) -> List[KnowledgeEntry]:
        categories_to_scan = [category] if category else self.CATEGORIES
        results: List[KnowledgeEntry] = []

        for cat in categories_to_scan:
            cat_val = cat.value if isinstance(cat, KnowledgeCategory) else str(cat)
            cat_dir = self.knowledge_dir / cat_val
            if not cat_dir.exists():
                continue

            for file_path in cat_dir.glob("*.json"):
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    c_enum = KnowledgeCategory(data.get("category", "lessons"))
                    data_copy = dict(data)
                    data_copy["category"] = c_enum
                    entry = KnowledgeEntry(**data_copy)

                    if tag and tag.lower() not in [t.lower() for t in entry.tags]:
                        continue
                    if query_text:
                        q = query_text.lower()
                        if q not in entry.title.lower() and q not in entry.summary.lower():
                            continue

                    results.append(entry)
                    if len(results) >= limit:
                        return results
                except Exception:
                    continue

        return results

    def get_knowledge_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for cat in self.CATEGORIES:
            cat_dir = self.knowledge_dir / cat.value
            count = len(list(cat_dir.glob("*.json"))) if cat_dir.exists() else 0
            summary[cat.value] = count
        return summary
