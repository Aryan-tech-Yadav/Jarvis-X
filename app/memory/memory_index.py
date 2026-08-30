"""In-memory index for high-value conversational and execution memories."""

from __future__ import annotations

import hashlib
import re
import time
from collections import defaultdict


class MemoryIndex:
    def __init__(self):
        self._entries = {}
        self._tokens = defaultdict(set)
        self._fingerprints = {}

    def add(self, content, *, kind="note", priority=0, importance=0.0, metadata=None, created_at=None):
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Memory content cannot be empty")
        normalized = " ".join(content.casefold().split())
        fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if fingerprint in self._fingerprints:
            return self._entries[self._fingerprints[fingerprint]]
        entry_id = fingerprint[:16]
        entry = {
            "id": entry_id, "content": content.strip(), "kind": kind,
            "priority": max(0, int(priority)), "importance": max(0.0, float(importance)),
            "metadata": dict(metadata or {}), "created_at": time.time() if created_at is None else float(created_at),
        }
        self._entries[entry_id] = entry
        self._fingerprints[fingerprint] = entry_id
        for token in self.tokens(content):
            self._tokens[token].add(entry_id)
        return entry

    def get(self, entry_id):
        return self._entries.get(entry_id)

    def candidates(self, query):
        identifiers = set()
        for token in self.tokens(query):
            identifiers.update(self._tokens.get(token, ()))
        return [self._entries[entry_id] for entry_id in identifiers]

    def entries(self):
        return list(self._entries.values())

    def remove(self, entry_id):
        entry = self._entries.pop(entry_id, None)
        if entry is None:
            return False
        normalized = " ".join(entry["content"].casefold().split())
        self._fingerprints.pop(hashlib.sha256(normalized.encode("utf-8")).hexdigest(), None)
        for token in self.tokens(entry["content"]):
            self._tokens[token].discard(entry_id)
        return True

    @staticmethod
    def tokens(value):
        return set(re.findall(r"[a-z0-9_]+", str(value).casefold()))
