class RiskReport:
    def build(self, risks, score, level):
        categories = sorted({item["category"] for item in risks})
        mitigations = {
            "security": "Run a threat model and security scan before deployment.",
            "performance": "Define load targets and test the critical realtime path.",
            "timeline": "Resolve the listed clarifying questions before planning implementation.",
            "scalability": "Document a scale-out path before committing to the data model.",
            "dependency": "Pin and audit third-party integrations.",
        }
        return {"score": score, "level": level, "categories": categories,
                "mitigations": [mitigations[item] for item in categories if item in mitigations]}
