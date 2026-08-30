import json


class ReflectionReport:
    def __init__(self, score, notes=None):
        self.score = score
        self.notes = list(notes or [])

    def to_dict(self):
        return {"scores": dict(self.score.scores), "overall": self.score.overall, "weakest_area": self.score.weakest_area, "notes": self.notes}

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)
