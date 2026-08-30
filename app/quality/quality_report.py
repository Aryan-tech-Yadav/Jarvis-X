"""Enterprise Quality Report Generator supporting Markdown, YAML, and JSON formats."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models.quality_result import (
    PerformanceResult,
    QualityScore,
    SecurityResult,
    StaticAnalysisResult,
)
from .models.repair_result import SelfHealingResult
from .models.test_result import TestSuiteResult


class QualityReport:
    """Produces executive and technical quality reports across formats."""

    def __init__(
        self,
        project_name: str = "Jarvis-X Project",
        quality_score: Optional[QualityScore] = None,
        static_result: Optional[StaticAnalysisResult] = None,
        test_suite_result: Optional[TestSuiteResult] = None,
        security_result: Optional[SecurityResult] = None,
        performance_result: Optional[PerformanceResult] = None,
        self_healing_result: Optional[SelfHealingResult] = None,
    ):
        self.project_name = project_name
        self.quality_score = quality_score
        self.static_result = static_result
        self.test_suite_result = test_suite_result
        self.security_result = security_result
        self.performance_result = performance_result
        self.self_healing_result = self_healing_result
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "quality_score": self.quality_score.to_dict() if self.quality_score else {},
            "static_analysis": self.static_result.to_dict() if self.static_result else {},
            "test_suite": self.test_suite_result.to_dict() if self.test_suite_result else {},
            "security": self.security_result.to_dict() if self.security_result else {},
            "performance": self.performance_result.to_dict() if self.performance_result else {},
            "self_healing": self.self_healing_result.to_dict() if self.self_healing_result else {},
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_yaml(self) -> str:
        data = self.to_dict()
        lines = [
            f"# Quality Report - {self.project_name}",
            f"timestamp: '{self.timestamp}'",
        ]
        if self.quality_score:
            qs = self.quality_score
            lines.extend([
                f"quality_score:",
                f"  overall_score: {qs.overall_score}",
                f"  grade: '{qs.grade}'",
                f"  passed_gate: {str(qs.passed_gate).lower()}",
                f"  critical_issues: {qs.critical_issues_count}",
                f"  warnings: {qs.warnings_count}",
                f"categories:",
            ])
            for cat_name, cs in qs.category_scores.items():
                lines.append(f"  {cat_name}: {cs.score}")

        if self.static_result:
            sr = self.static_result
            lines.extend([
                f"static_analysis:",
                f"  complexity: {sr.complexity_level}",
                f"  dead_files: {len(sr.dead_files)}",
                f"  duplicate_logic: {len(sr.duplicate_blocks)}",
                f"  circular_imports: {len(sr.circular_imports)}",
                f"  large_functions: {len(sr.large_functions)}",
            ])

        if self.test_suite_result:
            ts = self.test_suite_result
            lines.extend([
                f"testing:",
                f"  total: {ts.total_tests}",
                f"  passed: {ts.passed}",
                f"  failed: {ts.failed}",
                f"  coverage: '{ts.coverage.coverage_percentage}%'",
            ])

        if self.security_result:
            sec = self.security_result
            lines.extend([
                f"security:",
                f"  passed: {str(sec.passed).lower()}",
                f"  score: {sec.security_score}",
                f"  secrets_found: {sec.secrets_found}",
                f"  sql_injections: {sec.sql_injections}",
                f"  xss_risks: {sec.xss_risks}",
            ])

        if self.self_healing_result:
            sh = self.self_healing_result
            lines.extend([
                f"self_healing:",
                f"  repaired: {str(sh.final_success).lower()}",
                f"  attempts: {len(sh.repairs_attempted)}",
                f"  repair_time_sec: {sh.total_repair_time_sec}",
            ])

        return "\n".join(lines)

    def to_markdown(self) -> str:
        qs = self.quality_score
        status_stamp = "🟢 **RELEASE ACCEPTED**" if (qs and qs.passed_gate) else "🔴 **RELEASE REJECTED**"
        overall_val = f"{qs.overall_score:.1f} / 100" if qs else "N/A"
        grade_val = qs.grade if qs else "N/A"

        md = [
            f"# 🛡️ Autonomous Quality & Self-Healing Report",
            f"**Project:** `{self.project_name}` | **Generated:** `{self.timestamp}`",
            "",
            f"### Gate Status: {status_stamp} (Grade: `{grade_val}` | Score: `{overall_val}`)",
            "",
            "---",
            "",
            "## 📊 Category Scoreboard",
            "",
            "| Category | Score | Weight | Status |",
            "| :--- | :---: | :---: | :---: |",
        ]

        if qs:
            for cat_name, cs in qs.category_scores.items():
                cat_status = "✅ PASS" if cs.score >= 90.0 else ("⚠️ WARN" if cs.score >= 75.0 else "❌ FAIL")
                md.append(f"| **{cat_name.replace('_', ' ').title()}** | **{cs.score:.1f}** | {cs.weight:.2f} | {cat_status} |")

        md.extend([
            "",
            "---",
            "",
            "## 🔍 Static Analysis & Complexity",
        ])
        if self.static_result:
            sr = self.static_result
            md.extend([
                f"- **Complexity Level:** `{sr.complexity_level}` (Score: `{sr.complexity_score:.1f}`)",
                f"- **Dead Code / Orphan Files:** `{len(sr.dead_files)}` files, `{len(sr.dead_functions)}` functions",
                f"- **Duplicated Logic Blocks:** `{len(sr.duplicate_blocks)}`",
                f"- **Circular Imports:** `{len(sr.circular_imports)}` cycles detected",
                f"- **Large Functions / Classes:** `{len(sr.large_functions)}` functions, `{len(sr.large_classes)}` classes",
            ])

        md.extend([
            "",
            "---",
            "",
            "## 🧪 Test Suite & Coverage",
        ])
        if self.test_suite_result:
            ts = self.test_suite_result
            md.extend([
                f"- **Total Tests:** `{ts.total_tests}` (Passed: `{ts.passed}`, Failed: `{ts.failed}`, Errors: `{ts.errors}`)",
                f"- **Statement Coverage:** **`{ts.coverage.coverage_percentage:.1f}%`**",
                f"- **Execution Duration:** `{ts.duration_sec:.3f}s`",
            ])

        md.extend([
            "",
            "---",
            "",
            "## 🔒 Security Audit",
        ])
        if self.security_result:
            sec = self.security_result
            sec_badge = "✅ CLEAN" if sec.passed else "🚨 VULNERABILITIES DETECTED"
            md.extend([
                f"- **Security Status:** {sec_badge} (Score: `{sec.security_score:.1f}`)",
                f"- **Secrets Found:** `{sec.secrets_found}`",
                f"- **SQL Injections:** `{sec.sql_injections}`",
                f"- **XSS Risks:** `{sec.xss_risks}`",
                f"- **Unsafe Deserialization:** `{sec.deserialization_risks}`",
                f"- **Total Vulnerabilities:** `{len(sec.vulnerabilities)}`",
            ])

        md.extend([
            "",
            "---",
            "",
            "## ⚡ Performance Profiling",
        ])
        if self.performance_result:
            pr = self.performance_result
            md.extend([
                f"- **Performance Score:** `{pr.performance_score:.1f}`",
                f"- **Database Queries (Static N+1):** `{pr.db_query_count}`",
                f"- **Detected Bottlenecks:** `{len(pr.bottlenecks)}`",
            ])
            for sug in pr.suggestions[:3]:
                md.append(f"  - 💡 *{sug}*")

        if self.self_healing_result and self.self_healing_result.original_failed:
            sh = self.self_healing_result
            md.extend([
                "",
                "---",
                "",
                "## 🔧 Self-Healing & Automated Repair",
                f"- **Initial Failure:** `{sh.root_cause.failure if sh.root_cause else 'Unknown'}`",
                f"- **Root Cause:** `{sh.root_cause.root_cause if sh.root_cause else 'N/A'}`",
                f"- **Confidence:** `{sh.root_cause.confidence * 100:.0f}%`" if sh.root_cause else "",
                f"- **Repair Status:** {'✅ HEALED & RETESTED' if sh.final_success else '❌ REPAIR FAILED'}",
                f"- **Total Repair Time:** `{sh.total_repair_time_sec:.2f}s`",
                f"- **Attempts:** `{len(sh.repairs_attempted)}`",
            ])

        if qs and qs.suggestions:
            md.extend([
                "",
                "---",
                "",
                "## 💡 Actionable Suggestions & Recommendations",
            ])
            for s in qs.suggestions:
                md.append(f"- {s}")

        return "\n".join(md)
