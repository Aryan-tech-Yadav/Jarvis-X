class MilestoneTracker:
    def __init__(self, milestones=None):
        self.milestones = list(milestones or [])
        self.completed = set()

    def complete(self, milestone):
        if milestone in self.milestones:
            self.completed.add(milestone)

    def progress(self):
        total = len(self.milestones)
        return {"completed": len(self.completed), "total": total, "percent": (len(self.completed) / total * 100) if total else 100}