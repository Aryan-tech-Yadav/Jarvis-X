from app.memory.experience_memory import ExperienceMemory


class FailureMemory(ExperienceMemory):
    def record(self, error, context=None):
        return self.save({"error": error, "context": context or {}})