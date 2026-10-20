class ReasoningErrorClassifier:
    TYPES = {"syntax": "SyntaxError", "import": "ImportError", "runtime": "RuntimeError",
             "dependency": "DependencyError", "validation": "ValidationError"}

    def classify(self, error):
        text = str(error).casefold()
        for keyword, category in self.TYPES.items():
            if keyword in text:
                return category
        return "UnknownError"