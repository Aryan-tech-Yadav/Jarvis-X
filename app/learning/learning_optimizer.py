from app.learning.learning_score import LearningScore


class LearningOptimizer:
    def __init__(self, database, scorer=None):
        self.database = database
        self.scorer = scorer or LearningScore()

    def recommend(self):
        groups = self.database.by_area()
        if not groups:
            return {"weakest_area": None, "recommendation": "Collect execution outcomes first.", "confidence": 0.0}
        weakest = min(groups, key=lambda area: self.scorer.score(groups[area]))
        confidence = 1 - self.scorer.score(groups[weakest])
        return {"weakest_area": weakest, "recommendation": f"Improve {weakest.replace('_', ' ')} using recent failures.", "confidence": confidence}
