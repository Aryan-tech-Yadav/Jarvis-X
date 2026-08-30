class ErrorClassifier:
    KEYWORDS = {"syntax": "syntax", "import": "import", "module": "dependency", "validation": "validation", "security": "security", "runtime": "runtime"}

    def classify(self, error):
        text = str(error).casefold()
        for keyword, category in self.KEYWORDS.items():
            if keyword in text:
                return category
        return "logic"