from app.learning.lesson_store import LessonStore


class LearningMemory:
    def __init__(self, lesson_store=None):
        self.store = lesson_store or LessonStore()

    def remember(self, lesson, category="general", tags=None):
        return self.store.save_lesson({"lesson": lesson, "category": category, "tags": tags or []})

    def recall(self, query, limit=5):
        return self.store.search(query, limit)