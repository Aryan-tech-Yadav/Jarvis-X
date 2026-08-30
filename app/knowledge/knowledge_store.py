from __future__ import annotations

import hashlib
import time


class KnowledgeStore:
    def __init__(self):
        self._facts = {}
        self._fingerprints = {}

    def add(self, text, *, category="general", topics=None, confidence=0.5, metadata=None):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Fact text cannot be empty")
        normalized = " ".join(text.casefold().split())
        fingerprint = hashlib.sha256((normalized + category.casefold()).encode("utf-8")).hexdigest()
        if fingerprint in self._fingerprints:
            return self._facts[self._fingerprints[fingerprint]]
        fact_id = fingerprint[:16]
        fact = {
            "id": fact_id, "text": text.strip(), "category": category.strip() or "general",
            "topics": sorted({str(topic).casefold() for topic in (topics or []) if str(topic).strip()}),
            "confidence": min(1.0, max(0.0, float(confidence))), "metadata": dict(metadata or {}),
            "created_at": time.time(),
        }
        self._facts[fact_id] = fact
        self._fingerprints[fingerprint] = fact_id
        return fact

    def get(self, fact_id):
        return self._facts.get(fact_id)

    def all(self):
        return list(self._facts.values())
