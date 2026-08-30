class ResourceCost:
    def estimate(self, files=0, dependencies=0, memory_mb=None, cpu_seconds=None):
        complexity = max(0, int(files)) * 0.08 + max(0, int(dependencies)) * 0.6
        if memory_mb is not None:
            complexity += max(0.0, float(memory_mb)) / 1024
        if cpu_seconds is not None:
            complexity += max(0.0, float(cpu_seconds)) / 3600
        return {"resource_units": round(complexity, 2), "memory_mb": memory_mb, "cpu_seconds": cpu_seconds}
