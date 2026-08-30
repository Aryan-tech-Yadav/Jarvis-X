class RetryStrategy:
    def next_action(self, failed_action, error):
        action = str(failed_action).casefold()
        error = str(error).casefold()
        if "validation" in error:
            return "reflection"
        if "import" in error or "dependency" in error:
            return "dependency_fix"
        if "repair" in action:
            return "modify"
        if "modify" in action:
            return "repair"
        return "retry"