import json
import os


class KnowledgeCache:
    def __init__(self, path="data/knowledge_cache.json"):
        self.path = path
        self.entries = {}
        self._load()

    def get(self, source):
        return self.entries.get(source)

    def set(self, source, signature, document_id, project=None):
        entry = {"signature": signature, "document_id": document_id}
        if project:
            entry["project"] = project
        self.entries[source] = entry
        self.save()

    def remove(self, source):
        self.entries.pop(source, None)
        self.save()

    def save(self):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.entries, file, indent=2)

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                values = json.load(file)
            if isinstance(values, dict):
                self.entries = values
        except (OSError, json.JSONDecodeError):
            self.entries = {}