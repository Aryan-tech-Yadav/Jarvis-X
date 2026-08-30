class ChainOfThought:
    def __init__(self):
        self.thoughts = []

    def add(self, thought):
        value = thought.to_dict() if hasattr(thought, "to_dict") else dict(thought)
        if value not in self.thoughts:
            self.thoughts.append(value)
        return value

    def confidence_trend(self):
        return [item.get("confidence", 0.0) for item in self.thoughts]

    def history(self):
        return list(self.thoughts)