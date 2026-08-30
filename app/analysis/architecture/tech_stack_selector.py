class TechStackSelector:
    CANDIDATES = (
        ("FastAPI + React", {"backend": "FastAPI", "frontend": "React", "database": "PostgreSQL"}),
        ("Django + React", {"backend": "Django", "frontend": "React", "database": "PostgreSQL"}),
        ("Flask + Vue", {"backend": "Flask", "frontend": "Vue", "database": "PostgreSQL"}),
        ("Node + Next.js", {"backend": "Node.js", "frontend": "Next.js", "database": "PostgreSQL"}),
    )

    def select(self, requirements, intent):
        features = set(requirements.functional)
        scores = []
        for name, stack in self.CANDIDATES:
            score = 70
            if name == "FastAPI + React":
                score += 14 if intent["category"] == "Full Stack Web Application" else 8
                score += 7 if {"authentication", "search", "admin"} & features else 0
            if name == "Django + React":
                score += 13 if "admin" in features else 0
            if name == "Node + Next.js":
                score += 14 if "realtime" in features else 0
            if name == "Flask + Vue":
                score += 6 if intent["complexity"] == "low" else 0
            scores.append({"stack": name, "score": min(99, score), "components": stack})
        scores.sort(key=lambda item: item["score"], reverse=True)
        return {"selected": scores[0], "candidates": scores}
