"""Quality result contracts for static analysis, security, performance, and architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class QualityCategory(str, Enum):
    ARCHITECTURE = "architecture"
    CODE_QUALITY = "code_quality"
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"


@dataclass
class QualityIssue:
    file: str
    line: int
    rule: str
    message: str
    severity: IssueSeverity = IssueSeverity.MEDIUM
    category: QualityCategory = QualityCategory.CODE_QUALITY
    suggestion: str = ""
    remediation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity.value if isinstance(self.severity, IssueSeverity) else str(self.severity),
            "category": self.category.value if isinstance(self.category, QualityCategory) else str(self.category),
            "suggestion": self.suggestion,
            "remediation": self.remediation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QualityIssue:
        sev = data.get("severity", "medium")
        try:
            severity = IssueSeverity(sev)
        except ValueError:
            severity = IssueSeverity.MEDIUM

        cat = data.get("category", "code_quality")
        try:
            category = QualityCategory(cat)
        except ValueError:
            category = QualityCategory.CODE_QUALITY

        return cls(
            file=data.get("file", ""),
            line=int(data.get("line", 0)),
            rule=data.get("rule", ""),
            message=data.get("message", ""),
            severity=severity,
            category=category,
            suggestion=data.get("suggestion", ""),
            remediation=data.get("remediation", ""),
        )


@dataclass
class CategoryScore:
    category: QualityCategory
    score: float  # 0 to 100
    weight: float  # 0.0 to 1.0
    issues: List[QualityIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value if isinstance(self.category, QualityCategory) else str(self.category),
            "score": round(float(self.score), 2),
            "weight": round(float(self.weight), 3),
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": dict(self.metrics),
        }


@dataclass
class QualityScore:
    overall_score: float  # 0 to 100
    category_scores: Dict[str, CategoryScore] = field(default_factory=dict)
    grade: str = "A"  # A+, A, B, C, D, F
    passed_gate: bool = True
    gate_reasons: List[str] = field(default_factory=list)
    critical_issues_count: int = 0
    warnings_count: int = 0
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(float(self.overall_score), 2),
            "category_scores": {k: v.to_dict() for k, v in self.category_scores.items()},
            "grade": self.grade,
            "passed_gate": self.passed_gate,
            "gate_reasons": list(self.gate_reasons),
            "critical_issues_count": self.critical_issues_count,
            "warnings_count": self.warnings_count,
            "suggestions": list(self.suggestions),
        }


@dataclass
class StaticAnalysisResult:
    complexity_score: float = 100.0
    complexity_level: str = "Low"  # Low, Medium, High
    dead_files: List[str] = field(default_factory=list)
    dead_functions: List[Dict[str, Any]] = field(default_factory=list)
    duplicate_blocks: List[Dict[str, Any]] = field(default_factory=list)
    circular_imports: List[List[str]] = field(default_factory=list)
    large_functions: List[Dict[str, Any]] = field(default_factory=list)
    large_classes: List[Dict[str, Any]] = field(default_factory=list)
    unused_variables: List[Dict[str, Any]] = field(default_factory=list)
    architecture_violations: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[QualityIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "complexity_score": round(float(self.complexity_score), 2),
            "complexity_level": self.complexity_level,
            "dead_files": list(self.dead_files),
            "dead_functions": list(self.dead_functions),
            "duplicate_blocks": list(self.duplicate_blocks),
            "circular_imports": list(self.circular_imports),
            "large_functions": list(self.large_functions),
            "large_classes": list(self.large_classes),
            "unused_variables": list(self.unused_variables),
            "architecture_violations": list(self.architecture_violations),
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass
class SecurityResult:
    passed: bool = True
    security_score: float = 100.0  # 0 to 100
    vulnerabilities: List[QualityIssue] = field(default_factory=list)
    secrets_found: int = 0
    sql_injections: int = 0
    xss_risks: int = 0
    csrf_risks: int = 0
    deserialization_risks: int = 0
    config_issues: int = 0
    command_injections: int = 0
    scanned_files_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "security_score": round(float(self.security_score), 2),
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "secrets_found": self.secrets_found,
            "sql_injections": self.sql_injections,
            "xss_risks": self.xss_risks,
            "csrf_risks": self.csrf_risks,
            "deserialization_risks": self.deserialization_risks,
            "config_issues": self.config_issues,
            "command_injections": self.command_injections,
            "scanned_files_count": self.scanned_files_count,
        }


@dataclass
class PerformanceResult:
    performance_score: float = 100.0  # 0 to 100
    runtime_seconds: float = 0.0
    cpu_usage_pct: float = 0.0
    memory_bytes: int = 0
    disk_io_bytes: int = 0
    db_query_count: int = 0
    duplicate_queries: int = 0
    api_latency_ms: float = 0.0
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "performance_score": round(float(self.performance_score), 2),
            "runtime_seconds": round(float(self.runtime_seconds), 4),
            "cpu_usage_pct": round(float(self.cpu_usage_pct), 2),
            "memory_bytes": self.memory_bytes,
            "disk_io_bytes": self.disk_io_bytes,
            "db_query_count": self.db_query_count,
            "duplicate_queries": self.duplicate_queries,
            "api_latency_ms": round(float(self.api_latency_ms), 2),
            "bottlenecks": list(self.bottlenecks),
            "suggestions": list(self.suggestions),
        }
