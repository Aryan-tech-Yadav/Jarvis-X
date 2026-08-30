"""Similarity Engine for Jarvis-X.

Detects similar projects and enables reuse of:
  - architectures
  - folder structures
  - patterns
  - solutions

When user says "Build Clinic Management System", Jarvis:
  1. Searches memory for similar projects
  2. Finds "Hospital Management System" with 92% similarity
  3. Reuses architecture and adapts for clinic needs
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.intelligence.experience_engine import ExperienceEngine, ProjectExperience
from app.intelligence.project_memory import ProjectMemoryStore, ProjectMemory


@dataclass
class SimilarityResult:
    """Result of a similarity search."""

    project_name: str
    similarity_score: float
    experience: Optional[ProjectExperience] = None
    memory: Optional[ProjectMemory] = None
    matched_attributes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "similarity_score": self.similarity_score,
            "matched_attributes": list(self.matched_attributes),
        }


class SimilarityEngine:
    """Find similar past projects and enable reuse."""

    def __init__(self, experience_engine: Optional[ExperienceEngine] = None,
                 memory_store: Optional[ProjectMemoryStore] = None):
        self.experiences = experience_engine or ExperienceEngine()
        self.memory = memory_store or ProjectMemoryStore()

    def find_similar_projects(self, query: str, domain: Optional[str] = None,
                              limit: int = 5) -> List[SimilarityResult]:
        """Find projects similar to the query."""
        # Search experiences
        similar_experiences = self.experiences.search_similar(query, limit=limit * 2)
        # Search memories
        similar_memories = self.memory.find_similar(query, domain=domain, limit=limit * 2)

        results = []
        seen = set()

        for exp in similar_experiences:
            if exp.project_name in seen:
                continue
            seen.add(exp.project_name)
            # Compute similarity score
            score = self._compute_similarity(query, exp)
            matched = self._matched_attributes(query, exp)
            results.append(SimilarityResult(
                project_name=exp.project_name,
                similarity_score=score,
                experience=exp,
                matched_attributes=matched,
            ))

        for mem in similar_memories:
            key = f"{mem.project_name}:{mem.version}"
            if key in seen:
                continue
            seen.add(key)
            score = self._compute_memory_similarity(query, mem)
            matched = self._matched_memory_attributes(query, mem)
            results.append(SimilarityResult(
                project_name=mem.project_name,
                similarity_score=score,
                memory=mem,
                matched_attributes=matched,
            ))

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:max(1, limit)]

    def reuse_architecture(self, query: str) -> Optional[Dict[str, Any]]:
        """Reuse architecture from the most similar project."""
        similar = self.find_similar_projects(query, limit=1)
        if not similar:
            return None
        result = similar[0]
        if result.experience:
            return {
                "architecture": result.experience.architecture,
                "stack": result.experience.stack,
                "modules": result.experience.modules,
                "source_project": result.project_name,
                "similarity": result.similarity_score,
            }
        if result.memory:
            return {
                "architecture": result.memory.architecture,
                "folder_structure": result.memory.folder_structure,
                "stack": result.memory.stack,
                "source_project": result.project_name,
                "similarity": result.similarity_score,
            }
        return None

    def _compute_similarity(self, query: str, experience: ProjectExperience) -> float:
        """Compute similarity score between query and experience."""
        query_words = set(query.casefold().split())
        haystack = f"{experience.project_name} {experience.domain} {experience.architecture} {' '.join(experience.stack)} {' '.join(experience.modules)}".casefold()
        matches = sum(word in haystack for word in query_words)
        base = matches / max(1, len(query_words))
        # Boost by overall score
        return min(1.0, base + (experience.overall_score / 200.0))

    def _compute_memory_similarity(self, query: str, memory: ProjectMemory) -> float:
        """Compute similarity score between query and memory."""
        query_words = set(query.casefold().split())
        haystack = f"{memory.project_name} {memory.domain} {' '.join(memory.stack)}".casefold()
        matches = sum(word in haystack for word in query_words)
        base = matches / max(1, len(query_words))
        return min(1.0, base + (memory.overall_score / 200.0))

    def _matched_attributes(self, query: str, experience: ProjectExperience) -> List[str]:
        """Find which attributes matched between query and experience."""
        query_words = set(query.casefold().split())
        matched = []
        if any(w in experience.project_name.casefold() for w in query_words):
            matched.append("project_name")
        if any(w in experience.domain.casefold() for w in query_words):
            matched.append("domain")
        if any(w in experience.architecture.casefold() for w in query_words):
            matched.append("architecture")
        for tech in experience.stack:
            if any(w in tech.casefold() for w in query_words):
                matched.append("stack")
                break
        return matched

    def _matched_memory_attributes(self, query: str, memory: ProjectMemory) -> List[str]:
        """Find which attributes matched between query and memory."""
        query_words = set(query.casefold().split())
        matched = []
        if any(w in memory.project_name.casefold() for w in query_words):
            matched.append("project_name")
        if any(w in memory.domain.casefold() for w in query_words):
            matched.append("domain")
        for tech in memory.stack:
            if any(w in tech.casefold() for w in query_words):
                matched.append("stack")
                break
        return matched
