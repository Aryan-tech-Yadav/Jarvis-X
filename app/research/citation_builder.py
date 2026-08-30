class CitationBuilder:
    def build(self, findings):
        return sorted({item["source"] for item in findings})
