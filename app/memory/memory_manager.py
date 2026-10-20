import json
import os

from app.memory.memory_index import MemoryIndex
from app.memory.memory_search import MemorySearch
from app.memory.memory_cleaner import MemoryCleaner
from app.memory.memory_compressor import MemoryCompressor


class MemoryManager:

    def __init__(self):
        self.file = os.path.join("data", "memory.json")
        self.index = MemoryIndex()
        self.searcher = MemorySearch(self.index)
        self.compressor = MemoryCompressor()
        self.cleaner = MemoryCleaner()

    def load_memory(self):
        try:
            with open(self.file, "r", encoding="utf-8") as file:
                return json.load(file)

        except (OSError, json.JSONDecodeError):
            return {}

    def save_memory(self, key, value):
        memory = self.load_memory()
        memory[key] = value
        self._write_memory(memory)
        return True

    def get_memory(self, key):
        memory = self.load_memory()
        return memory.get(key, None)

    def add_message(self, role, content):
        memory = self.load_memory()
        history = memory.setdefault("conversation_history", [])
        history.append({"role": role, "content": content})
        self._write_memory(memory)
        if isinstance(content, str) and content.strip():
            self.index.add(content, kind="conversation", metadata={"role": role})
        return True

    def remember(self, content, priority=0, importance=0.0, metadata=None):
        """Store a deduplicated, searchable in-process memory entry."""
        return self.index.add(content, priority=priority, importance=importance, metadata=metadata)

    def search_memory(self, query, limit=5):
        return self.searcher.search(query, limit)

    def compress_history(self, max_entries=10):
        return MemoryCompressor(max_entries=max_entries).compress(self.get_history())

    def clean_index(self, max_age_seconds=None, max_entries=None):
        cleaner = MemoryCleaner(max_age_seconds=max_age_seconds, max_entries=max_entries)
        kept = cleaner.clean(self.index.entries())
        kept_ids = {entry["id"] for entry in kept}
        for entry in list(self.index.entries()):
            if entry["id"] not in kept_ids:
                self.index.remove(entry["id"])
        return kept

    def get_history(self):
        return self.load_memory().get("conversation_history", [])

    def add_reasoning(self, entry):
        memory = self.load_memory()
        memory.setdefault("reasoning", []).append(entry)
        self._write_memory(memory)
        return True

    def get_reasoning(self):
        return self.load_memory().get("reasoning", [])

    def clear_history(self):
        memory = self.load_memory()
        memory["conversation_history"] = []
        self._write_memory(memory)
        return True

    def _write_memory(self, memory):
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        with open(self.file, "w", encoding="utf-8") as file:
            json.dump(memory, file, indent=4)
        
