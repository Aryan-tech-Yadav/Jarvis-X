class WorkspaceMetrics:
    TERMINAL = {"completed", "failed"}

    def calculate(self, projects):
        projects = list(projects)
        completed = [item for item in projects if item.status == "completed"]
        failed = [item for item in projects if item.status == "failed"]
        runtimes = [float(item.metrics.get("runtime_seconds", 0)) for item in projects if item.metrics.get("runtime_seconds") is not None]
        return {
            "projects": len(projects),
            "completed": len(completed),
            "failed": len(failed),
            "active": len([item for item in projects if item.status not in self.TERMINAL]),
            "average_runtime_seconds": sum(runtimes) / len(runtimes) if runtimes else 0.0,
            "repair_count": sum(int(item.metrics.get("repair_count", 0)) for item in projects),
            "benchmarks": sum(int(item.metrics.get("benchmarks", 0)) for item in projects),
        }
