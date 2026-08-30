class LearningScore:
    def score(self, outcomes):
        values = list(outcomes)
        if not values:
            return 1.0
        return sum(bool(item.get("success")) for item in values) / len(values)
