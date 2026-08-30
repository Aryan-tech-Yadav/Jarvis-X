class ReleaseReport:
    """Human-readable release summary derived from the machine manifest."""

    def to_markdown(self, manifest):
        gates = manifest["gates"]
        lines = [
            "# Jarvis-X Release Report",
            "",
            f"- Status: {'PASSED' if manifest['success'] else 'BLOCKED'}",
            f"- Version: {manifest['version']}",
            f"- Created: {manifest['created_at']}",
            "",
            "## Quality gates",
            "",
        ]
        lines.extend(f"- {'PASS' if gate['passed'] else 'FAIL'} {name}: {gate['summary']}" for name, gate in gates.items())
        lines.extend([
            "",
            "## Benchmarks",
            "",
            f"- Projects: {manifest['benchmarks']['total']}",
            f"- Preflight rate: {manifest['benchmarks']['preflight_rate']:.0%}",
            f"- Approval required: {manifest['benchmarks']['approval_required']}",
        ])
        return "\n".join(lines)
