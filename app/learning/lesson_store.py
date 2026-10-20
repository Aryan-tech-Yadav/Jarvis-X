import hashlib
import json
import os

from config import LESSONS_PATH


class LessonStore:
    def __init__(self, path=None):
        self.path = path or LESSONS_PATH
        self.lessons = []
        self._load()

    def save_lesson(self, lesson):
        if not isinstance(lesson, dict) or not lesson.get("lesson"):
            raise ValueError("Lesson must contain lesson text")
        key = self._key(lesson)
        for stored in self.lessons:
            if stored.get("key") == key:
                stored["occurrences"] = stored.get("occurrences", 1) + 1
                stored.setdefault("tags", [])
                stored["tags"] = sorted(set(stored["tags"]) | set(lesson.get("tags", [])))
                self._save()
                return False
        stored = dict(lesson)
        stored["key"] = key
        stored["occurrences"] = 1
        self.lessons.append(stored)
        self._save()
        return True

    def get_lessons(self, limit=None):
        values = list(self.lessons)
        return values[-limit:] if limit is not None else values

    def search(self, query, limit=5):
        terms = str(query).casefold().split()
        matches = [(sum(term in str(lesson).casefold() for term in terms), lesson)
                   for lesson in self.lessons]
        matches = [(score, lesson) for score, lesson in matches if score]
        matches.sort(key=lambda pair: pair[0], reverse=True)
        return [lesson for _, lesson in matches[:max(0, limit)]]

    def _key(self, lesson):
        content = f"{lesson.get('category', '')}|{lesson['lesson']}".casefold().strip()
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                values = json.load(file)
            self.lessons = [value for value in values if isinstance(value, dict) and value.get("lesson")]
        except (OSError, json.JSONDecodeError):
            self.lessons = []

    def _save(self):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.lessons, file, indent=2)