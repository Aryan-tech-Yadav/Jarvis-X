class TechnologySelector:
    def select(self, requirements):
        features = set(requirements.get("features", ()))
        constraints = set(requirements.get("constraints", ()))
        database = "PostgreSQL" if "payments" in features or "scale" in constraints else "SQLite"
        return {
            "backend": "FastAPI",
            "frontend": "React" if len(features) >= 3 else "server-rendered templates",
            "database": database,
            "cache": "Redis" if "realtime" in features or "scale" in constraints else None,
        }
