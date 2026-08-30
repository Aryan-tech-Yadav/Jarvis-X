"""Enhanced Memory Layer - Semantic memory and user profile.

Layer 4 of the 5-layer AI Agent architecture.
Extends MemoryManager with:
  - Vector/semantic memory
  - User profile and preferences
  - Memory-LLM integration
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.memory.memory_manager import MemoryManager
from app.memory.memory_search import MemorySearch
from app.memory.memory_index import MemoryIndex


@dataclass
class UserProfile:
    """Persistent user profile."""
    name: str = ""
    preferred_language: str = "english"
    preferences: Dict[str, Any] = field(default_factory=dict)
    habits: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    last_seen: str = ""


class SemanticMemory:
    """Semantic memory layer using embeddings.

    Provides similarity-based retrieval over stored memories.
    Falls back to lexical search if embeddings are unavailable.
    """

    def __init__(self, memory_manager: MemoryManager, embedding_provider=None):
        self.memory_manager = memory_manager
        self.embedding_provider = embedding_provider
        self._embeddings: Dict[str, List[float]] = {}
        self._index_loaded = False

    def initialize(self):
        """Load existing embeddings."""
        try:
            emb_file = os.path.join("data", "embeddings.json")
            if os.path.exists(emb_file):
                with open(emb_file, "r", encoding="utf-8") as f:
                    self._embeddings = json.load(f)
                self._index_loaded = True
        except Exception:
            pass

    def add(self, content: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Add content with embedding."""
        embedding = self._get_embedding(content)
        if embedding:
            entry_id = metadata.get("id") if metadata else None
            if entry_id:
                self._embeddings[entry_id] = embedding
            self._save_embeddings()
        return None

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Semantic search over memories."""
        query_emb = self._get_embedding(query)
        if not query_emb:
            return []

        scored = []
        for entry_id, emb in self._embeddings.items():
            score = self._cosine_similarity(query_emb, emb)
            scored.append((score, entry_id))

        scored.sort(reverse=True)
        results = []
        for score, entry_id in scored[:limit]:
            results.append({
                "id": entry_id,
                "score": score,
                "content": "",
                "metadata": {},
            })

        return results

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text."""
        if self.embedding_provider:
            try:
                return self.embedding_provider.embed(text)
            except Exception:
                pass

        return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> List[float]:
        """Simple hash-based embedding fallback."""
        words = text.lower().split()
        vec = [0.0] * 64
        for i, word in enumerate(words):
            h = hash(word) % 64
            vec[h] += 1.0
            if i + 1 < len(words):
                bigram = f"{words[i]}_{words[i+1]}"
                h2 = hash(bigram) % 64
                vec[h2] += 0.5
        return vec

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = sum(x * x for x in a) ** 0.5
        mag_b = sum(y * y for y in b) ** 0.5
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def _save_embeddings(self):
        """Persist embeddings to disk."""
        try:
            os.makedirs("data", exist_ok=True)
            with open(os.path.join("data", "embeddings.json"), "w", encoding="utf-8") as f:
                json.dump(self._embeddings, f)
        except Exception:
            pass


class UserProfileManager:
    """Manages persistent user profile and preferences."""

    def __init__(self):
        self.profile_file = os.path.join("data", "user_profile.json")
        self.profile = self._load()

    def _load(self) -> UserProfile:
        """Load user profile from disk."""
        try:
            with open(self.profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return UserProfile(**data)
        except Exception:
            return UserProfile()

    def save(self):
        """Persist user profile to disk."""
        try:
            os.makedirs(os.path.dirname(self.profile_file), exist_ok=True)
            with open(self.profile_file, "w", encoding="utf-8") as f:
                json.dump({
                    "name": self.profile.name,
                    "preferred_language": self.profile.preferred_language,
                    "preferences": self.profile.preferences,
                    "habits": self.profile.habits,
                    "relationships": self.profile.relationships,
                    "created_at": self.profile.created_at,
                    "last_seen": self.profile.last_seen,
                }, f, indent=2)
        except Exception:
            pass

    def get_name(self) -> str:
        return self.profile.name

    def set_name(self, name: str):
        self.profile.name = name
        self.save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.profile.preferences.get(key, default)

    def set_preference(self, key: str, value: Any):
        self.profile.preferences[key] = value
        self.save()

    def add_habit(self, habit: str):
        if habit not in self.profile.habits:
            self.profile.habits.append(habit)
            self.save()

    def get_habits(self) -> List[str]:
        return list(self.profile.habits)

    def update_last_seen(self):
        from datetime import datetime
        self.profile.last_seen = datetime.now().isoformat()
        self.save()

    def to_context(self) -> Dict[str, Any]:
        """Convert profile to context dict for LLM prompts."""
        return {
            "user_name": self.profile.name,
            "language": self.profile.preferred_language,
            "preferences": self.profile.preferences,
            "habits": self.profile.habits[:5],
        }


class EnhancedMemoryManager:
    """Enhanced memory manager with semantic search and user profile.

    Extends MemoryManager with:
      - Semantic/similarity-based memory retrieval
      - User profile and preferences
      - Memory consolidation
      - Memory injection into LLM context
    """

    def __init__(self):
        self.memory = MemoryManager()
        self.semantic = SemanticMemory(self.memory)
        self.user_profile = UserProfileManager()
        self._initialized = False

    def initialize(self):
        """Initialize all memory subsystems."""
        if self._initialized:
            return
        self.memory.load_memory()
        self.semantic.initialize()
        self.user_profile.update_last_seen()
        self._initialized = True

    def remember(self, content: str, priority: int = 0, importance: float = 0.0,
                 metadata: Dict[str, Any] = None) -> bool:
        """Store a memory with semantic indexing."""
        result = self.memory.remember(content, priority, importance, metadata)
        self.semantic.add(content, metadata or {})
        return result

    def search(self, query: str, limit: int = 5, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """Search memories using hybrid lexical + semantic search."""
        lexical = self.memory.search_memory(query, limit=limit)

        if use_semantic:
            semantic = self.semantic.search(query, limit=limit)
            combined = {m.get("id") or m.get("content", "")[:50]: m for m in lexical}
            for m in semantic:
                key = m.get("id", "")
                if key not in combined:
                    combined[key] = m

            results = list(combined.values())
            results.sort(key=lambda m: m.get("score", m.get("importance", 0)), reverse=True)
            return results[:limit]

        return lexical

    def add_message(self, role: str, content: str):
        """Add conversation message."""
        self.memory.add_message(role, content)

    def get_conversation_context(self, max_messages: int = 10) -> str:
        """Get recent conversation as context string."""
        history = self.memory.get_history()
        recent = history[-max_messages:] if len(history) > max_messages else history
        return "\n".join(f"{m['role']}: {m['content']}" for m in recent)

    def get_user_context(self) -> Dict[str, Any]:
        """Get user profile as context for LLM."""
        return self.user_profile.to_context()

    def get_full_context(self, query: str = "", max_memories: int = 3) -> Dict[str, Any]:
        """Get complete context: user profile + relevant memories + conversation."""
        memories = self.search(query, limit=max_memories) if query else []
        return {
            "user": self.get_user_context(),
            "memories": memories,
            "conversation": self.get_conversation_context(max_messages=5),
        }

    def inject_into_prompt(self, base_prompt: str, query: str = "") -> str:
        """Inject memory context into an LLM prompt."""
        context = self.get_full_context(query)
        user_name = context.get("user", {}).get("user_name", "")
        user_section = f"User: {user_name}\n" if user_name else ""

        memory_section = ""
        if context.get("memories"):
            memory_items = [m.get("content", "") for m in context["memories"][:3]]
            memory_section = "\nRelevant memories:\n" + "\n".join(f"- {m}" for m in memory_items if m) + "\n"

        conversation_section = ""
        if context.get("conversation"):
            conversation_section = f"\nRecent conversation:\n{context['conversation']}\n"

        return f"""{base_prompt}

{user_section}{memory_section}{conversation_section}"""
