from app.memory.experience_memory import ExperienceMemory


class PatternLibrary(ExperienceMemory):
    def add(self, name, pattern):
        return self.save({"name": name, "pattern": pattern})

    def get(self, name):
        matches = self.find(name)
        return matches[0] if matches else None