"""Autonomous Security Engine for Static Vulnerability Scanning."""

from __future__ import annotations

import ast
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models.quality_result import (
    IssueSeverity,
    QualityCategory,
    QualityIssue,
    SecurityResult,
)


class SecurityEngine:
    """Scans codebases for secrets, injection flaws, unsafe deserialization, and misconfigurations."""

    IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}

    # Secret scanning patterns
    SECRET_PATTERNS = [
        (re.compile(r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|access[_-]?token|password|passwd|private[_-]?key)\s*=\s*['\"]([A-Za-z0-9_\-./+=]{10,})['\"]"), "hardcoded_secret", IssueSeverity.CRITICAL),
        (re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"), "private_key_exposed", IssueSeverity.CRITICAL),
        (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "openai_api_key", IssueSeverity.CRITICAL),
        (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "github_personal_token", IssueSeverity.CRITICAL),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "aws_access_key", IssueSeverity.CRITICAL),
        (re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"), "slack_token", IssueSeverity.CRITICAL),
    ]

    # Weak Crypto patterns
    WEAK_HASH_PATTERNS = [
        (re.compile(r"hashlib\.(?:md5|sha1)\("), "weak_hash_algorithm", IssueSeverity.HIGH, "Use hashlib.sha256() or argon2 for secure hashing"),
    ]

    # SSL / Debug Misconfigs
    MISCONFIG_PATTERNS = [
        (re.compile(r"verify\s*=\s*False"), "disabled_ssl_verification", IssueSeverity.HIGH, "Enable SSL verification (verify=True) in production requests"),
        (re.compile(r"(?i)debug\s*=\s*True"), "debug_mode_enabled", IssueSeverity.MEDIUM, "Disable debug mode (DEBUG = False) for production deployments"),
        (re.compile(r"['\"]Access-Control-Allow-Origin['\"]\s*,\s*['\"]\*['\"]"), "overly_permissive_cors", IssueSeverity.MEDIUM, "Restrict CORS Allow-Origin to trusted domains"),
    ]

    def __init__(self, root_path: Optional[str] = None):
        self.root_path = Path(root_path).resolve() if root_path else Path.cwd()

    def scan_directory(self, target_dir: Optional[str] = None) -> SecurityResult:
        dir_path = Path(target_dir).resolve() if target_dir else self.root_path
        py_files = self._collect_python_files(dir_path)

        vulnerabilities: List[QualityIssue] = []
        secrets_count = 0
        sqli_count = 0
        xss_count = 0
        csrf_count = 0
        deserialization_count = 0
        config_count = 0
        cmd_injection_count = 0

        for file_path in py_files:
            rel_path = str(file_path.relative_to(dir_path)).replace("\\", "/")
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=rel_path)
            except SyntaxError as e:
                vulnerabilities.append(
                    QualityIssue(
                        file=rel_path,
                        line=e.lineno or 1,
                        rule="unparseable_code",
                        message=f"Syntax error prevents security AST analysis: {e.msg}",
                        severity=IssueSeverity.HIGH,
                        category=QualityCategory.SECURITY,
                        suggestion="Fix Python syntax",
                    )
                )
                continue

            # 1. Regex-based pattern scans (Secrets & Misconfigs)
            file_vulns, s_cnt, cfg_cnt = self._scan_text_patterns(rel_path, content)
            vulnerabilities.extend(file_vulns)
            secrets_count += s_cnt
            config_count += cfg_cnt

            # 2. AST-based security analysis
            ast_vulns, counts = self._scan_ast_nodes(rel_path, tree, content)
            vulnerabilities.extend(ast_vulns)
            sqli_count += counts.get("sqli", 0)
            xss_count += counts.get("xss", 0)
            csrf_count += counts.get("csrf", 0)
            deserialization_count += counts.get("deser", 0)
            cmd_injection_count += counts.get("cmd", 0)
            config_count += counts.get("cfg", 0)

        # Calculate security score (0-100)
        critical_count = len([v for v in vulnerabilities if v.severity == IssueSeverity.CRITICAL])
        high_count = len([v for v in vulnerabilities if v.severity == IssueSeverity.HIGH])
        medium_count = len([v for v in vulnerabilities if v.severity == IssueSeverity.MEDIUM])
        low_count = len([v for v in vulnerabilities if v.severity == IssueSeverity.LOW])

        penalty = (critical_count * 30.0) + (high_count * 15.0) + (medium_count * 5.0) + (low_count * 1.0)
        security_score = max(0.0, 100.0 - penalty)
        passed = (critical_count == 0 and high_count == 0)

        return SecurityResult(
            passed=passed,
            security_score=round(security_score, 2),
            vulnerabilities=vulnerabilities,
            secrets_found=secrets_count,
            sql_injections=sqli_count,
            xss_risks=xss_count,
            csrf_risks=csrf_count,
            deserialization_risks=deserialization_count,
            config_issues=config_count,
            command_injections=cmd_injection_count,
            scanned_files_count=len(py_files),
        )

    def _collect_python_files(self, dir_path: Path) -> List[Path]:
        if dir_path.is_file() and dir_path.suffix == ".py":
            return [dir_path]
        py_files: List[Path] = []
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]
            for file in files:
                if file.endswith(".py"):
                    py_files.append(Path(root) / file)
        return py_files


    def _scan_text_patterns(self, rel_path: str, content: str) -> Tuple[List[QualityIssue], int, int]:
        issues: List[QualityIssue] = []
        secrets_cnt = 0
        cfg_cnt = 0

        # Scan for Secrets
        for pattern, rule_name, severity in self.SECRET_PATTERNS:
            for match in pattern.finditer(content):
                line_no = content[:match.start()].count("\n") + 1
                secrets_cnt += 1
                issues.append(
                    QualityIssue(
                        file=rel_path,
                        line=line_no,
                        rule=rule_name,
                        message=f"Possible hardcoded credential or secret detected: '{match.group(0)[:25]}...'",
                        severity=severity,
                        category=QualityCategory.SECURITY,
                        suggestion="Load sensitive tokens from environment variables or a secrets manager",
                        remediation="Use os.environ.get('API_KEY') instead of hardcoding",
                    )
                )

        # Scan for Weak Crypto
        for pattern, rule_name, severity, remed in self.WEAK_HASH_PATTERNS:
            for match in pattern.finditer(content):
                line_no = content[:match.start()].count("\n") + 1
                cfg_cnt += 1
                issues.append(
                    QualityIssue(
                        file=rel_path,
                        line=line_no,
                        rule=rule_name,
                        message=f"Use of cryptographically weak hashing algorithm: '{match.group(0)}'",
                        severity=severity,
                        category=QualityCategory.SECURITY,
                        suggestion="Upgrade to SHA-256, SHA-3, or Argon2/Bcrypt for password hashing",
                        remediation=remed,
                    )
                )

        # Scan for Misconfigurations
        for pattern, rule_name, severity, remed in self.MISCONFIG_PATTERNS:
            for match in pattern.finditer(content):
                line_no = content[:match.start()].count("\n") + 1
                cfg_cnt += 1
                issues.append(
                    QualityIssue(
                        file=rel_path,
                        line=line_no,
                        rule=rule_name,
                        message=f"Security misconfiguration detected: '{match.group(0)}'",
                        severity=severity,
                        category=QualityCategory.SECURITY,
                        suggestion=remed,
                        remediation=remed,
                    )
                )

        return issues, secrets_cnt, cfg_cnt

    def _scan_ast_nodes(self, rel_path: str, tree: ast.AST, content: str) -> Tuple[List[QualityIssue], Dict[str, int]]:
        issues: List[QualityIssue] = []
        counts = {"sqli": 0, "xss": 0, "csrf": 0, "deser": 0, "cmd": 0, "cfg": 0}

        for node in ast.walk(tree):
            # 1. SQL Injection Detection
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                # execute / raw / cursor calls with formatted strings
                if func_name in {"execute", "executemany", "raw", "raw_query"} and node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, (ast.JoinedStr, ast.BinOp)):  # f-string or % or +
                        counts["sqli"] += 1
                        issues.append(
                            QualityIssue(
                                file=rel_path,
                                line=node.lineno,
                                rule="sql_injection",
                                message=f"Potential SQL injection via dynamic string formatting in '{func_name}()'.",
                                severity=IssueSeverity.CRITICAL,
                                category=QualityCategory.SECURITY,
                                suggestion="Use parameterized queries / prepared statements",
                                remediation="cursor.execute('SELECT * FROM table WHERE id = %s', (val,))",
                            )
                        )

                # 2. Dynamic Code Execution (eval / exec)
                if func_name in {"eval", "exec"}:
                    counts["cmd"] += 1
                    issues.append(
                        QualityIssue(
                            file=rel_path,
                            line=node.lineno,
                            rule="dynamic_code_execution",
                            message=f"Dangerous dynamic execution with '{func_name}()'.",
                            severity=IssueSeverity.CRITICAL,
                            category=QualityCategory.SECURITY,
                            suggestion="Avoid dynamic execution or use ast.literal_eval() for safe data parsing",
                            remediation="Use ast.literal_eval() or explicit data structures",
                        )
                    )

                # 3. Command Injection (os.system / subprocess.Popen with shell=True)
                if func_name in {"system", "popen"}:
                    if isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", "") == "os":
                        counts["cmd"] += 1
                        issues.append(
                            QualityIssue(
                                file=rel_path,
                                line=node.lineno,
                                rule="command_injection",
                                message=f"Dangerous system command execution via 'os.{func_name}()'.",
                                severity=IssueSeverity.CRITICAL,
                                category=QualityCategory.SECURITY,
                                suggestion="Use subprocess.run() with a list of arguments and shell=False",
                                remediation="subprocess.run(['cmd', 'arg1'], check=True)",
                            )
                        )

                if func_name in {"Popen", "call", "check_call", "run"}:
                    # Check for shell=True
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            counts["cmd"] += 1
                            issues.append(
                                QualityIssue(
                                    file=rel_path,
                                    line=node.lineno,
                                    rule="subprocess_shell_true",
                                    message=f"Subprocess invoked with shell=True in '{func_name}()'.",
                                    severity=IssueSeverity.HIGH,
                                    category=QualityCategory.SECURITY,
                                    suggestion="Pass command arguments as an array and set shell=False",
                                    remediation="subprocess.run(['executable', 'arg'], shell=False)",
                                )
                            )

                # 4. Unsafe Deserialization (pickle.loads, yaml.load)
                if func_name in {"load", "loads"}:
                    mod_id = ""
                    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                        mod_id = node.func.value.id
                    if mod_id in {"pickle", "_pickle", "cPickle", "marshal", "shelve"}:
                        counts["deser"] += 1
                        issues.append(
                            QualityIssue(
                                file=rel_path,
                                line=node.lineno,
                                rule="unsafe_deserialization_pickle",
                                message=f"Unsafe deserialization using '{mod_id}.{func_name}()'.",
                                severity=IssueSeverity.CRITICAL,
                                category=QualityCategory.SECURITY,
                                suggestion="Use safe serialization formats like JSON, MessagePack, or Protocol Buffers",
                                remediation="json.loads(data)",
                            )
                        )
                    elif mod_id == "yaml" and func_name == "load":
                        has_safe_loader = any(kw.arg == "Loader" and "Safe" in ast.unparse(kw.value) for kw in node.keywords if hasattr(ast, "unparse"))
                        if not has_safe_loader:
                            counts["deser"] += 1
                            issues.append(
                                QualityIssue(
                                    file=rel_path,
                                    line=node.lineno,
                                    rule="unsafe_yaml_load",
                                    message="yaml.load() without SafeLoader allows arbitrary code execution.",
                                    severity=IssueSeverity.CRITICAL,
                                    category=QualityCategory.SECURITY,
                                    suggestion="Use yaml.safe_load()",
                                    remediation="yaml.safe_load(stream)",
                                )
                            )

                # 5. XSS / Unescaped Template Rendering
                if func_name in {"render_template_string", "Markup"}:
                    if node.args and isinstance(node.args[0], (ast.JoinedStr, ast.BinOp)):
                        counts["xss"] += 1
                        issues.append(
                            QualityIssue(
                                file=rel_path,
                                line=node.lineno,
                                rule="xss_unescaped_template",
                                message=f"Possible XSS vulnerability in '{func_name}()' with dynamic string formatting.",
                                severity=IssueSeverity.HIGH,
                                category=QualityCategory.SECURITY,
                                suggestion="Escape dynamic variables before rendering in HTML context",
                                remediation="html.escape(user_input)",
                            )
                        )

        return issues, counts
