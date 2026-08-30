from app.memory.memory_manager import MemoryManager


class ProgressManager:

    def __init__(self, memory=None):
        self.memory = memory or MemoryManager()

    def start(self, goal, steps, project_path):
        progress = {
            "goal": goal,
            "project_path": project_path,
            "steps": list(steps),
            "completed": [],
            "current": steps[0] if steps else None,
            "remaining": list(steps),
        }
        self._save(progress)
        return progress

    def complete_step(self, step):
        progress = self.get()
        if not progress:
            return None

        if step not in progress["completed"]:
            progress["completed"].append(step)
        progress["remaining"] = [
            item for item in progress["steps"]
            if item not in progress["completed"]
        ]
        progress["current"] = progress["remaining"][0] if progress["remaining"] else None
        self._save(progress)
        return progress

    def resume(self, goal, steps, project_path):
        progress = self.get()
        if (
            not progress
            or progress.get("goal") != goal
            or progress.get("project_path") != project_path
            or progress.get("steps") != list(steps)
        ):
            return self.start(goal, steps, project_path)

        progress.pop("error", None)
        progress["remaining"] = [
            step for step in progress["steps"]
            if step not in progress["completed"]
        ]
        progress["current"] = progress["remaining"][0] if progress["remaining"] else None
        self._save(progress)
        return progress

    def fail_step(self, step, error):
        progress = self.get()
        if not progress:
            return None

        progress["current"] = step
        progress["error"] = error
        self._save(progress)
        return progress

    def get(self):
        return self.memory.get_memory("project_progress")

    def clear(self):
        self.memory.save_memory("project_progress", None)
        return True

    def _save(self, progress):
        self.memory.save_memory("project_progress", progress)
