from app.learning.experience_manager import ExperienceManager
from app.learning.pattern_extractor import PatternExtractor
from app.learning.learning_memory import LearningMemory
from app.core.logger import Logger


class LearningEngine:
    def __init__(self, experience_manager=None, pattern_extractor=None, learning_memory=None, learning_database=None):
        self.experiences = experience_manager or ExperienceManager()
        self.extractor = pattern_extractor or PatternExtractor()
        self.memory = learning_memory or LearningMemory()
        self.database = learning_database

    def learn(self, context, success=True):
        if not success:
            return {"success": False, "learned": False, "reason": "Failed tasks are not stored"}
        experience = self.extractor.extract(context)
        if not experience.get("goal"):
            return {"success": False, "learned": False, "reason": "Experience has no goal"}
        learned = self.experiences.save_experience(experience)
        if self.database is not None:
            self.database.record({"area": "execution", "success": True, "goal": experience["goal"]})
        lesson = self.memory.remember(
            experience["summary"],
            category="project_pattern",
            tags=experience.get("agent_sequence", []),
        )
        Logger.info(f"Learned experience for: {experience['goal']}")
        return {"success": True, "learned": learned, "lesson_saved": lesson, "experience": experience}

    def learn_from_task(self, context, success=True):
        return self.learn(context, success)

    def recall(self, query, limit=5):
        return self.experiences.search(query, limit)
