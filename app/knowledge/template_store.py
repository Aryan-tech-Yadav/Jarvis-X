"""Template store and retriever for RAG-based code generation.

Stores high-quality project templates and retrieves similar ones
to guide AI code generation.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProjectTemplate:
    """A high-quality project template."""
    template_id: str
    name: str
    description: str
    project_type: str
    tech_stack: Dict[str, Any]
    files: Dict[str, str]  # filename -> content
    config: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    quality_score: float = 95.0
    usage_count: int = 0
    embedding: Optional[List[float]] = None


class TemplateStore:
    """Persistent storage for project templates."""

    def __init__(self, store_path: str = "data/templates"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, ProjectTemplate] = {}
        self._load_all()

    def _load_all(self):
        """Load all templates from disk."""
        for template_file in self.store_path.glob("*.json"):
            try:
                data = json.loads(template_file.read_text(encoding="utf-8"))
                template = ProjectTemplate(**data)
                self._templates[template.template_id] = template
            except Exception:
                pass

    def save(self, template: ProjectTemplate) -> bool:
        """Save template to disk."""
        try:
            self._templates[template.template_id] = template
            file_path = self.store_path / f"{template.template_id}.json"
            payload = {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "project_type": template.project_type,
                "tech_stack": template.tech_stack,
                "files": template.files,
                "config": template.config,
                "tags": template.tags,
                "quality_score": template.quality_score,
                "usage_count": template.usage_count,
            }
            file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def get(self, template_id: str) -> Optional[ProjectTemplate]:
        """Get template by ID."""
        return self._templates.get(template_id)

    def list(self, project_type: str = "") -> List[ProjectTemplate]:
        """List all templates, optionally filtered by project type."""
        templates = list(self._templates.values())
        if project_type:
            templates = [t for t in templates if t.project_type == project_type]
        return sorted(templates, key=lambda t: t.quality_score, reverse=True)

    def record_usage(self, template_id: str):
        """Record template usage for ranking."""
        template = self._templates.get(template_id)
        if template:
            template.usage_count += 1
            self.save(template)

    def add_template(self, template: ProjectTemplate) -> bool:
        """Add a new template."""
        return self.save(template)


class TemplateRetriever:
    """Retrieve relevant templates for a given project request.

    Uses hybrid search: keyword matching + semantic similarity.
    """

    def __init__(self, template_store: Optional[TemplateStore] = None):
        self.store = template_store or TemplateStore()

    def retrieve(self, query: str, project_type: str = "", limit: int = 3) -> List[ProjectTemplate]:
        """Retrieve templates relevant to the query.

        Args:
            query: User's project request
            project_type: Optional project type filter
            limit: Maximum templates to return

        Returns:
            List of relevant templates sorted by relevance
        """
        candidates = self.store.list(project_type)
        if not candidates:
            return []

        scored = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for template in candidates:
            score = self._score_template(template, query, query_words)
            scored.append((score, template))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:limit]]

    def _score_template(self, template: ProjectTemplate, query: str, query_words: set) -> float:
        """Score template relevance to query."""
        score = 0.0

        # Keyword overlap
        desc_words = set(template.description.lower().split())
        name_words = set(template.name.lower().split())
        tag_words = set(" ".join(template.tags).lower().split())

        overlap = len(query_words & (desc_words | name_words | tag_words))
        score += overlap * 10.0

        # Project type match
        if template.project_type in query.lower():
            score += 20.0

        # Quality bonus
        score += template.quality_score * 0.1

        # Usage bonus (popular templates rank higher)
        score += min(template.usage_count * 0.5, 10.0)

        # Exact name match
        if template.name.lower() in query.lower():
            score += 30.0

        return score

    def get_best_template(self, query: str, project_type: str = "") -> Optional[ProjectTemplate]:
        """Get the single best template for a query."""
        results = self.retrieve(query, project_type, limit=1)
        return results[0] if results else None


class TemplateAugmentedGenerator:
    """Generate code using retrieved templates as context.

    Combines RAG with LLM generation for higher quality output.
    """

    def __init__(self, retriever: Optional[TemplateRetriever] = None, ai_manager=None):
        self.retriever = retriever or TemplateRetriever()
        self.ai_manager = ai_manager

    def generate_with_context(self, user_prompt: str, project_type: str = "") -> Dict[str, Any]:
        """Generate project code augmented with retrieved templates.

        Returns:
            Dict with files, tech_stack, and template_id
        """
        template = self.retriever.get_best_template(user_prompt, project_type)

        if not template:
            return {
                "files": {},
                "tech_stack": {},
                "template_id": None,
                "augmented": False,
            }

        # Record usage
        self.retriever.store.record_usage(template.template_id)

        return {
            "files": template.files,
            "tech_stack": template.tech_stack,
            "template_id": template.template_id,
            "template_name": template.name,
            "augmented": True,
            "base_template": template.template_id,
        }

    def build_augmented_prompt(self, user_prompt: str, template: ProjectTemplate) -> str:
        """Build an LLM prompt augmented with template context."""
        template_context = f"""
Reference Template: {template.name}
Description: {template.description}
Tech Stack: {template.tech_stack}

Reference Files:
"""
        for filename, content in list(template.files.items())[:5]:
            template_context += f"\n--- {filename} ---\n{content[:2000]}\n"

        return f"""{template_context}

User Request: {user_prompt}

Instructions:
1. Use the reference template structure and patterns above
2. Generate production-ready code following the same architecture
3. Do NOT create placeholder methods or TODO comments
4. Every imported module must exist in the project
5. Every called function must be implemented
6. Return complete, runnable code only
7. Follow the tech stack: {template.tech_stack}

Generate the complete project files now."""
