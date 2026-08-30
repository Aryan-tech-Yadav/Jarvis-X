import os
import shutil
import tracemalloc


class ResourceMonitor:
    """Portable, dependency-free resource signals for runtime health checks."""

    def __init__(self, path="."):
        self.path = path
        if not tracemalloc.is_tracing():
            tracemalloc.start()

    def sample(self):
        current, peak = tracemalloc.get_traced_memory()
        disk = shutil.disk_usage(self.path)
        return {
            "process_memory_bytes": current,
            "process_peak_memory_bytes": peak,
            "disk_free_bytes": disk.free,
            "disk_total_bytes": disk.total,
            "cpu_count": os.cpu_count() or 1,
        }
