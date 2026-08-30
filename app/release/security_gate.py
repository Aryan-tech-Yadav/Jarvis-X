import ast
import os
import re


class SecurityGate:
    """A lightweight release gate for high-confidence static security signals."""

    IGNORED_DIRECTORIES = {".git", ".venv", "venv", "__pycache__", "workspace", "test-workspace"}
    SECRET_ASSIGNMENT = re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]")

    def scan(self, root):
        root = os.path.abspath(root)
        findings = []
        files_scanned = 0
        for directory, directories, files in os.walk(root):
            directories[:] = [name for name in directories if name not in self.IGNORED_DIRECTORIES]
            for filename in files:
                if filename.endswith(".py"):
                    files_scanned += 1
                    findings.extend(self._scan_file(os.path.join(directory, filename), root))
        high = [item for item in findings if item["severity"] == "high"]
        return {"passed": not high, "findings": findings, "high_severity": len(high), "files_scanned": files_scanned}

    def _scan_file(self, path, root):
        relative = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            with open(path, "r", encoding="utf-8") as source:
                content = source.read()
            tree = ast.parse(content, filename=relative)
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            return [{"file": relative, "line": 0, "severity": "high", "rule": "unreadable_or_invalid_python", "message": str(error)}]
        findings = []
        for match in self.SECRET_ASSIGNMENT.finditer(content):
            findings.append({"file": relative, "line": content[:match.start()].count("\n") + 1, "severity": "high", "rule": "hardcoded_secret", "message": "Possible hardcoded credential."})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                findings.append({"file": relative, "line": node.lineno, "severity": "high", "rule": "dynamic_execution", "message": f"{node.func.id}() must not be used in release code."})
        return findings
