from time import time


class KernelScheduler:
    """Graph-aware scheduling policy for priority, dependencies, delays, and retries.

    It selects work only. Dispatch is intentionally owned by ``KernelDispatcher``
    so scheduling cannot accidentally invoke side-effecting handlers.
    """

    def __init__(self, graph, resource_manager=None, clock=None, max_parallel=1, default_retries=0):
        if max_parallel < 1:
            raise ValueError("max_parallel must be at least one")
        self.graph = graph
        self.resource_manager = resource_manager
        self.clock = clock or time
        self.max_parallel = int(max_parallel)
        self.default_retries = max(0, int(default_retries))

    def next_batch(self, context, *, now=None, max_parallel=None):
        now = self.clock() if now is None else float(now)
        capacity = self.max_parallel if max_parallel is None else max(1, int(max_parallel))
        candidates = self.graph.ready(context.completed_nodes)
        selected = []
        paused = []
        for node in candidates:
            node_id = node["id"]
            if context.delayed_until.get(node_id, 0.0) > now:
                continue
            decision = self._admit(node, open_tasks=len(selected))
            if not decision.get("allowed", True):
                paused.append({"node": node_id, "reason": decision.get("reason", "resource limit")})
                context.record("KERNEL_NODE_PAUSED", paused[-1])
                continue
            if decision.get("warnings"):
                context.warnings.extend(item for item in decision["warnings"] if item not in context.warnings)
            selected.append(node)
            if len(selected) >= capacity:
                break
        return {"nodes": selected, "paused": paused}

    def retry_or_fail(self, context, node, *, now=None):
        node_id = node["id"]
        payload = node.get("payload") if isinstance(node.get("payload"), dict) else {}
        retry_limit = max(0, int(payload.get("max_retries", self.default_retries)))
        if context.attempts.get(node_id, 0) <= retry_limit:
            delay = max(0.0, float(payload.get("retry_delay_seconds", 0.0)))
            if delay:
                moment = self.clock() if now is None else float(now)
                context.delay(node_id, moment + delay)
            context.record("KERNEL_NODE_RETRY_SCHEDULED", {"node_id": node_id, "retry": context.attempts.get(node_id, 0)})
            return True
        return False

    def snapshot(self):
        return {"max_parallel": self.max_parallel, "default_retries": self.default_retries,
                "graph": self.graph.to_dict()}

    def _admit(self, node, open_tasks):
        if self.resource_manager is None:
            return {"allowed": True, "warnings": []}
        method = getattr(self.resource_manager, "scheduling_decision", None) or getattr(self.resource_manager, "admit", None)
        if method is None:
            return {"allowed": True, "warnings": []}
        decision = method(priority=node.get("priority", 0), open_tasks=open_tasks)
        return dict(decision or {"allowed": True})
