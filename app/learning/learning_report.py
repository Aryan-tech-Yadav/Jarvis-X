import json


class LearningReport:
    def __init__(self, recommendation):
        self.recommendation = dict(recommendation)

    def to_dict(self):
        return dict(self.recommendation)

    def to_json(self):
        return json.dumps(self.recommendation, indent=2)
