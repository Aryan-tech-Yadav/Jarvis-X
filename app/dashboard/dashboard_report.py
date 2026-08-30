import json


class DashboardReport:
    def __init__(self, metrics):
        self.metrics = dict(metrics)

    def to_dict(self):
        return dict(self.metrics)

    def to_json(self):
        return json.dumps(self.metrics, indent=2, sort_keys=True)

    def to_markdown(self):
        return "\n".join(["# Jarvis-X Dashboard", "", *[f"- {name.replace('_', ' ').title()}: {value}" for name, value in sorted(self.metrics.items())]])
