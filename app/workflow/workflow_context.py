from copy import deepcopy


class WorkflowContext:
    """Mutable per-run context kept separate from the workflow definition."""

    def __init__(self, goal, values=None):
        self._values = {"goal": goal, "outputs": {}, "signals": {}}
        self._values.update(deepcopy(values or {}))
        self._values.setdefault("outputs", {})
        self._values.setdefault("signals", {})

    def has_signal(self, name):
        return bool(self._values["signals"].get(name))

    def record(self, step_id, result):
        value = dict(result or {})
        self._values["outputs"][step_id] = value
        self._values["signals"].update(value.get("signals", {}))
        self._values.update(value.get("context", {}))

    def to_dict(self):
        return deepcopy(self._values)
