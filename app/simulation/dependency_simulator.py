class DependencySimulator:
    FEATURE_DEPENDENCIES = {
        "authentication": ("python-jose", "passlib"),
        "database": ("sqlalchemy",),
        "uploads": ("python-multipart",),
        "realtime": ("websockets",),
        "payments": ("stripe",),
    }

    def estimate(self, requirements, architecture=None):
        dependencies = set()
        for feature in requirements.get("features", ()):
            dependencies.update(self.FEATURE_DEPENDENCIES.get(feature, ()))
        technology = (architecture or {}).get("technology", {})
        backend = technology.get("backend")
        if backend == "FastAPI":
            dependencies.add("fastapi")
        if technology.get("database") == "PostgreSQL":
            dependencies.add("psycopg")
        return sorted(dependencies)
