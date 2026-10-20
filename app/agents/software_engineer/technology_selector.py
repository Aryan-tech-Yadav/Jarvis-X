"""Technology selection facade."""

from app.engineering.technology_selector import TechnologySelector as EngineeringTechnologySelector


class TechnologySelector:
    def __init__(self, selector=None):
        self.selector = selector or EngineeringTechnologySelector()

    def select(self, requirements):
        return self.selector.select(requirements.to_dict())

