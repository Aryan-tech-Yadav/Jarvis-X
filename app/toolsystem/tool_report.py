"""Tool Orchestration execution report generator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ToolReport:
    """Produces structured markdown and dictionary reports of tool executions."""

    @staticmethod
    def generate_report(metrics_summary: Dict[str, Any]) -> str:
        lines = [
            "### 🛠️ Tool Orchestration & Execution Report",
            "",
            "| Tool | Calls | Success | Rate | Avg Duration | Retries | Status |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
        for tool_name, data in metrics_summary.items():
            rate = data.get("success_rate_pct", 100.0)
            badge = "🟢 PASS" if rate >= 95.0 else ("⚠️ WARN" if rate >= 80.0 else "❌ FAIL")
            lines.append(
                f"| **{tool_name.title()}** | {data.get('total_calls', 0)} | {data.get('success_count', 0)} | {rate:.1f}% | {data.get('average_duration_sec', 0.0):.3f}s | {data.get('retries_count', 0)} | {badge} |"
            )
        return "\n".join(lines)
