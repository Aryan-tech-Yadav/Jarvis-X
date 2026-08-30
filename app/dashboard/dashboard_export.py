import csv
import json


class DashboardExport:
    def json(self, report):
        values = report.to_dict() if hasattr(report, "to_dict") else dict(report)
        return json.dumps(values, indent=2, sort_keys=True)

    def csv(self, report):
        values = report.to_dict() if hasattr(report, "to_dict") else dict(report)
        rows = [["metric", "value"], *[[key, value] for key, value in sorted(values.items())]]
        # csv.writer needs a file-like object; build RFC4180-safe simple scalar output.
        return "\n".join(",".join(csv_quote(item) for item in row) for row in rows)


def csv_quote(value):
    text = str(value).replace('"', '""')
    return f'"{text}"'
