from config import MAX_RETRY


class ProjectRetry:

    def __init__(self, max_attempts=MAX_RETRY):
        self.max_attempts = max(1, int(max_attempts))

    def attempts(self):
        return range(self.max_attempts)
        