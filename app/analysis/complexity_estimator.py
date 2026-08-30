class ComplexityEstimator:
    def estimate(self, intent, requirements, architecture, risk):
        endpoints = len(architecture["endpoints"])
        tables = len(architecture["entities"])
        files = max(intent["estimated_modules"] * 2, endpoints + tables + 8)
        classes = max(4, tables + len(requirements.functional))
        minutes = files * 4 + int(risk.get("score", 0))
        return {"level": intent["complexity"], "estimated_files": files, "estimated_classes": classes,
                "estimated_endpoints": endpoints, "estimated_tables": tables, "estimated_minutes": minutes,
                "risk_score": risk.get("score", 0)}
