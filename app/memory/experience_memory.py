from app.memory.memory_manager import MemoryManager


class ExperienceMemory:
    def __init__(self, memory=None, key="experiences"):
        self.memory = memory or MemoryManager()
        self.key = key

    def save(self, experience):
        values = self.memory.get_memory(self.key) or []
        if experience not in values:
            values.append(experience)
        self.memory.save_memory(self.key, values)
        return experience

    def find(self, goal):
        return [item for item in (self.memory.get_memory(self.key) or []) if goal.casefold() in str(item).casefold()]