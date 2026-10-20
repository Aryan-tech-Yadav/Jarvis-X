class FailureRecovery:
    def __init__(self, max_retries=2):
        self.max_retries = max(0, max_retries)

    def decide(self, retry_count, error):
        if retry_count < self.max_retries:
            return "retry"
        return "stop"