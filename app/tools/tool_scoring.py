class ToolScoring:
    def score(self, tool, capability, history=None):
        text = f"{getattr(tool, 'name', '')} {getattr(tool, 'description', '')}".casefold()
        matches = sum(term in text for term in str(capability).casefold().split())
        return matches + getattr(tool, "priority", 0) / 100