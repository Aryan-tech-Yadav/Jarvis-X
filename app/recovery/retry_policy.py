class RetryPolicy:
    DEFAULTS = {"research": 5, "validation": 2, "build": 3, "runtime": 4}

    def __init__(self, limits=None):
        self.limits = {**self.DEFAULTS, **(limits or {})}

    def can_retry(self, category, attempt):
        return attempt < self.limits.get(category, 1)