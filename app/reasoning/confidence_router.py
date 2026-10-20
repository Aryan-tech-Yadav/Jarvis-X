class ConfidenceRouter:
    def route(self, confidence):
        value = float(confidence)
        if value >= 0.95:
            return "execute"
        if value >= 0.80:
            return "reflect"
        if value >= 0.60:
            return "critic"
        if value >= 0.40:
            return "ask_user"
        return "stop"