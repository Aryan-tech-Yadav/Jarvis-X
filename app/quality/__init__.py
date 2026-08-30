"""Jarvis-X Autonomous QA & Self-Healing System (EPIC-004)."""

from .benchmark_validator import BenchmarkValidator
from .models import (
    CategoryScore,
    CoverageResult,
    IssueSeverity,
    Patch,
    PerformanceResult,
    QualityCategory,
    QualityIssue,
    QualityScore,
    RepairAttempt,
    RootCauseAnalysis,
    SecurityResult,
    SelfHealingResult,
    StaticAnalysisResult,
    TestCaseResult,
    TestSuiteResult,
    TestType,
)
from .performance_engine import PerformanceEngine
from .qa_engine import QAEngine, StaticAnalyzer
from .quality_report import QualityReport
from .quality_score import QualityScoreEngine
from .repair_engine import RepairEngine, SelfRepairMemory
from .root_cause_engine import RootCauseEngine
from .security_engine import SecurityEngine
from .test_engine import TestEngine, TestGenerator
from .validation_engine import ValidationEngine

__all__ = [
    # Engines
    "QAEngine",
    "StaticAnalyzer",
    "TestEngine",
    "TestGenerator",
    "SecurityEngine",
    "PerformanceEngine",
    "RootCauseEngine",
    "RepairEngine",
    "SelfRepairMemory",
    "QualityScoreEngine",
    "QualityReport",
    "BenchmarkValidator",
    "ValidationEngine",
    # Models
    "IssueSeverity",
    "QualityCategory",
    "QualityIssue",
    "CategoryScore",
    "QualityScore",
    "StaticAnalysisResult",
    "SecurityResult",
    "PerformanceResult",
    "TestType",
    "TestCaseResult",
    "CoverageResult",
    "TestSuiteResult",
    "RootCauseAnalysis",
    "Patch",
    "RepairAttempt",
    "SelfHealingResult",
]
from .lifecycle_gate import (
    LifecycleGateResult,
    LifecycleQualityGate,
    REQUIRED_STAGES,
    StageResult,
)

__all__ += [
    "LifecycleGateResult",
    "LifecycleQualityGate",
    "REQUIRED_STAGES",
    "StageResult",
]
