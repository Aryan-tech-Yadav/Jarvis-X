"""Self-improvement package for Jarvis-X.

Enables autonomous self-improvement:
- Project scanning
- Dependency graph analysis
- Quality checking
- Improvement planning
- Risk assessment
- Sandbox testing
- Benchmark comparison
- AI code review
- Evolution orchestration
- Version management
- Metrics tracking
- Report generation
"""

from app.self_improvement.analyzer import SystemAnalyzer
from app.self_improvement.project_scanner import ProjectScanner, ProjectScanResult
from app.self_improvement.dependency_graph import DependencyGraphBuilder, DependencyGraph
from app.self_improvement.quality_checker import QualityChecker, FileQualityReport
from app.self_improvement.planner import ImprovementPlanner, ImprovementPlan, ImprovementTask
from app.self_improvement.risk_engine import RiskEngine, RiskAssessment
from app.self_improvement.sandbox import SandboxBuilder, Sandbox
from app.self_improvement.benchmark import BenchmarkEngine, BenchmarkResult
from app.self_improvement.comparator import BenchmarkComparator
from app.self_improvement.reviewer import AICodeReviewer, CodeReview
from app.self_improvement.evolution_engine import SelfEvolutionEngine
from app.self_improvement.version_manager import VersionManager, ProjectVersion
from app.self_improvement.metrics import EvolutionMetricsTracker, EvolutionMetrics
from app.self_improvement.report_generator import EvolutionReportGenerator, EvolutionReport
from app.self_improvement.evolution_db import EvolutionDB, EvolutionRecord

__all__ = [
    "SystemAnalyzer",
    "ProjectScanner",
    "ProjectScanResult",
    "DependencyGraphBuilder",
    "DependencyGraph",
    "QualityChecker",
    "FileQualityReport",
    "ImprovementPlanner",
    "ImprovementPlan",
    "ImprovementTask",
    "RiskEngine",
    "RiskAssessment",
    "SandboxBuilder",
    "Sandbox",
    "BenchmarkEngine",
    "BenchmarkResult",
    "BenchmarkComparator",
    "AICodeReviewer",
    "CodeReview",
    "SelfEvolutionEngine",
    "VersionManager",
    "ProjectVersion",
    "EvolutionMetricsTracker",
    "EvolutionMetrics",
    "EvolutionReportGenerator",
    "EvolutionReport",
    "EvolutionDB",
    "EvolutionRecord",
]
