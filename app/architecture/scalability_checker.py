class ScalabilityChecker:
    def check(self, plan):
        warnings = []
        if plan["technology"].get("database") == "SQLite" and "uploads" in plan["requirements"].get("features", ()):
            warnings.append("Use object storage and a migration path before high-volume uploads.")
        if "realtime" in plan["requirements"].get("features", ()) and not plan["technology"].get("cache"):
            warnings.append("Realtime workloads need a message broker or cache-backed coordination layer.")
        return warnings
