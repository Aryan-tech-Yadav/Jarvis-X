class RiskScore:
    def calculate(self, risks):
        return min(100, sum(item["score"] for item in risks))

    @staticmethod
    def level(score):
        return "high" if score >= 60 else "medium" if score >= 25 else "low"
