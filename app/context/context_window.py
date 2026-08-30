class ContextWindow:
    def __init__(self, conversations=10, reasoning=5):
        self.conversations = conversations
        self.reasoning = reasoning

    def apply(self, context):
        result = dict(context)
        result["conversation"] = list(context.get("conversation", []))[-self.conversations:]
        result["reasoning"] = list(context.get("reasoning", []))[-self.reasoning:]
        return result