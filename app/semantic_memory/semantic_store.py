import json
import os

from config import SEMANTIC_MEMORY_PATH
from app.semantic_memory.models import SemanticMemory


class SemanticStore:
    """Small JSON store with an explicit in-memory cache and safe malformed-file handling."""

    def __init__(self, path=None):
        self.path = path or SEMANTIC_MEMORY_PATH
        self._memories = {}
        self._load()

    def add(self, memory):
        if not isinstance(memory, SemanticMemory):
            raise TypeError("memory must be a SemanticMemory")
        self._memories[memory.memory_id] = memory
        self.save()
        return memory

    def get(self, memory_id):
        return self._memories.get(memory_id)

    def all(self):
        return sorted(self._memories.values(), key=lambda item: (item.updated_at, item.memory_id), reverse=True)

    def find_duplicate(self, content, memory_type):
        key = (content.casefold(), memory_type.casefold())
        for memory in self._memories.values():
            if (memory.content.casefold(), memory.memory_type) == key:
                return memory
        return None

    def save(self):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump([memory.to_dict() for memory in self.all()], file, indent=2, sort_keys=True)

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                values = json.load(file)
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(values, list):
            return
        for value in values:
            try:
                memory = SemanticMemory.from_dict(value)
            except (TypeError, ValueError):
                continue
            self._memories[memory.memory_id] = memory
