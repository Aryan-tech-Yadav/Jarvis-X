import json


class ExecutionReport:
    """Builds portable JSON/Markdown reports from execution state rather than logs."""

    def build(self, context, *, graph=None, monitor=None, status=None):
        snapshot = monitor.snapshot() if monitor is not None else {}
        graph_data = graph.to_dict() if graph is not None and hasattr(graph, "to_dict") else graph or {}
        return {
            "run_id": context.run_id,
            "goal": context.goal,
            "status": status or context.state.value,
            "state": context.state.value,
            "completed_nodes": list(context.completed_nodes),
            "failed_node": context.failed_node,
            "metrics": dict(context.metrics),
            "errors": list(context.errors),
            "warnings": list(context.warnings),
            "artifacts": list(context.artifacts),
            "timeline": list(context.timeline),
            "graph": graph_data,
            "monitor": snapshot,
        }

    @staticmethod
    def to_json(report):
        return json.dumps(report, indent=2, sort_keys=True, default=str)

    @staticmethod
    def to_markdown(report):
        lines = ["# Jarvis-X Execution Report", "", "- Run: " + str(report["run_id"]),
                 "- Status: " + str(report["status"]), "- State: " + str(report["state"]),
                 "- Completed nodes: " + str(len(report["completed_nodes"])),
                 "- Failed node: " + str(report["failed_node"] or "none")]
        if report["errors"]:
            lines.extend(["", "## Errors", *["- " + str(item) for item in report["errors"]]])
        return "\n".join(lines)
