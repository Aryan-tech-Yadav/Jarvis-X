import hashlib
import json
import os
from config import EXPERIENCES_PATH


class ExperienceManager:
    def __init__(self, path=None):
        self.path = path or EXPERIENCES_PATH
        self.experiences = []
        self._load()

    def save_experience(self, experience):
        if not isinstance(experience, dict) or not experience.get("goal"):
            raise ValueError("Experience must contain a goal")
        fingerprint = self._fingerprint(experience)
        if any(item.get("fingerprint") == fingerprint for item in self.experiences):
            return False
        stored = dict(experience)
        stored["fingerprint"] = fingerprint
        self.experiences.append(stored)
        self._save()
        return True

    def add_experience(self, experience):
        return self.save_experience(experience)

    def get_experiences(self, limit=None):
        items = list(self.experiences)
        return items[-limit:] if limit is not None else items

    def search(self, query, limit=5):
        words = set(str(query).casefold().split())
        ranked = []
        for item in self.experiences:
            haystack = f"{item.get('goal', '')} {item.get('summary', '')}".casefold()
            score = sum(word in haystack for word in words)
            if score:
                ranked.append((score, item))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in ranked[:max(0, limit)]]

    def _fingerprint(self, experience):
        content = json.dumps(experience, sort_keys=True, default=str)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                values = json.load(file)
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(values, list):
            self.experiences = [item for item in values if isinstance(item, dict) and item.get("goal")]

    def _save(self):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.experiences, file, indent=2)