class DependencyOptimizer:
    def order(self, steps):
        by_name = {self._name(step): step for step in steps}
        remaining = {name: set(self._dependencies(step)) & set(by_name) for name, step in by_name.items()}
        ordered = []
        while remaining:
            ready = sorted(name for name, dependencies in remaining.items() if not dependencies)
            if not ready:
                raise ValueError("Circular step dependency detected")
            for name in ready:
                ordered.append(by_name[name])
                remaining.pop(name)
            for dependencies in remaining.values():
                dependencies.difference_update(ready)
        return ordered

    @staticmethod
    def _name(step):
        return str(step.get("name") if isinstance(step, dict) else step)

    @staticmethod
    def _dependencies(step):
        return step.get("dependencies", ()) if isinstance(step, dict) else ()
