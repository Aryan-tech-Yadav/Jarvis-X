"""Error Intelligence - Advanced error understanding and recovery.

Week 3: Error Intelligence
Har error ke liye:
  Error -> Category -> Root Cause -> Known Solution? -> Auto Fix -> Verify -> Learn

Error Knowledge Base banao.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


class ErrorCategory(str, Enum):
    """Error categories."""
    SYNTAX = "syntax"
    IMPORT = "import"
    ATTRIBUTE = "attribute"
    NAME = "name"
    TYPE = "type"
    VALUE = "value"
    MATH = "math"
    RUNTIME = "runtime"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONFIG = "config"
    NETWORK = "network"
    DATABASE = "database"
    UNKNOWN = "unknown"


@dataclass
class ErrorAnalysis:
    """Analysis of an error."""
    error_id: str
    category: ErrorCategory
    root_cause: str
    severity: str = "medium"  # low, medium, high, critical
    affected_file: str = ""
    affected_line: int = 0
    stack_trace: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class ErrorSolution:
    """Solution for an error."""
    solution_id: str
    error_pattern: str
    fix_description: str
    fix_code: str = ""
    confidence: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    created_at: str = ""


class ErrorKnowledgeBase:
    """Persistent storage for error solutions."""

    def __init__(self, kb_path: str = "data/knowledge/error_kb.json"):
        self.kb_path = Path(kb_path)
        self.kb_path.parent.mkdir(parents=True, exist_ok=True)
        self._solutions: Dict[str, ErrorSolution] = {}
        self._load()

    def _load(self):
        """Load solutions from disk."""
        if self.kb_path.exists():
            try:
                with open(self.kb_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for sol_id, entry in data.items():
                        self._solutions[sol_id] = ErrorSolution(
                            solution_id=entry["solution_id"],
                            error_pattern=entry["error_pattern"],
                            fix_description=entry["fix_description"],
                            fix_code=entry.get("fix_code", ""),
                            confidence=entry.get("confidence", 0.0),
                            success_count=entry.get("success_count", 0),
                            failure_count=entry.get("failure_count", 0),
                            created_at=entry.get("created_at", ""),
                        )
            except Exception:
                pass

    def _save(self):
        """Save solutions to disk."""
        try:
            data = {}
            for sol_id, sol in self._solutions.items():
                data[sol_id] = {
                    "solution_id": sol.solution_id,
                    "error_pattern": sol.error_pattern,
                    "fix_description": sol.fix_description,
                    "fix_code": sol.fix_code,
                    "confidence": sol.confidence,
                    "success_count": sol.success_count,
                    "failure_count": sol.failure_count,
                    "created_at": sol.created_at,
                }
            with open(self.kb_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def lookup(self, error_message: str) -> Optional[ErrorSolution]:
        """Look up solution for error."""
        error_lower = error_message.lower()
        for sol in self._solutions.values():
            if sol.error_pattern.lower() in error_lower:
                return sol
        return None

    def add_solution(self, solution: ErrorSolution):
        """Add solution to knowledge base."""
        self._solutions[solution.solution_id] = solution
        self._save()

    def record_outcome(self, solution_id: str, success: bool):
        """Record outcome of applying a solution."""
        sol = self._solutions.get(solution_id)
        if sol:
            if success:
                sol.success_count += 1
            else:
                sol.failure_count += 1
            total = sol.success_count + sol.failure_count
            sol.confidence = (sol.success_count / total) * 100.0 if total > 0 else 0.0
            self._save()

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        total = len(self._solutions)
        successful = sum(1 for s in self._solutions.values() if s.success_count > 0)
        return {
            "total_solutions": total,
            "successful_solutions": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }


class ErrorIntelligence:
    """Advanced error understanding and recovery.

    Pipeline:
      Error -> Category -> Root Cause -> Known Solution? -> Auto Fix -> Verify -> Learn
    """

    def __init__(self, event_bus=None, ai_router=None):
        self.event_bus = event_bus
        self.ai_router = ai_router
        self.kb = ErrorKnowledgeBase()
        self._error_history: List[ErrorAnalysis] = []

    def analyze(self, error: Exception, context: Dict[str, Any] = None) -> ErrorAnalysis:
        """Analyze an error.

        Args:
            error: Exception object
            context: Error context

        Returns:
            ErrorAnalysis with category, root cause, and solution
        """
        error_message = str(error)
        error_type = type(error).__name__
        context = context or {}

        # Step 1: Categorize
        category = self._categorize(error_message, error_type)
        self._emit("ERROR_CATEGORIZED", {"category": category.value})

        # Step 2: Root cause analysis
        root_cause = self._analyze_root_cause(error_message, error_type, category, context)
        self._emit("ERROR_ANALYZED", {"root_cause": root_cause})

        # Step 3: Look up known solution
        known_solution = self.kb.lookup(error_message)
        if known_solution:
            self._emit("ERROR_KNOWN_SOLUTION_FOUND", {"solution_id": known_solution.solution_id})
        else:
            self._emit("ERROR_UNKNOWN", {"error": error_message[:100]})

        analysis = ErrorAnalysis(
            error_id=f"err_{int(time.time())}_{hash(error_message) % 10000}",
            category=category,
            root_cause=root_cause,
            severity=self._determine_severity(category, error_message),
            affected_file=context.get("file", ""),
            affected_line=context.get("line", 0),
            stack_trace=context.get("traceback", ""),
            context=context,
            timestamp=datetime.now().isoformat(),
        )

        self._error_history.append(analysis)
        return analysis

    def _categorize(self, error_message: str, error_type: str) -> ErrorCategory:
        """Categorize error."""
        error_lower = error_message.lower()

        if "modulenotfounderror" in error_lower or "no module named" in error_lower:
            return ErrorCategory.IMPORT
        if "importerror" in error_lower:
            return ErrorCategory.IMPORT
        if "syntaxerror" in error_lower or "invalid syntax" in error_lower:
            return ErrorCategory.SYNTAX
        if "attributeerror" in error_lower:
            return ErrorCategory.ATTRIBUTE
        if "nameerror" in error_lower or "is not defined" in error_lower:
            return ErrorCategory.NAME
        if "typeerror" in error_lower or "type mismatch" in error_lower:
            return ErrorCategory.TYPE
        if "valueerror" in error_lower or "invalid value" in error_lower:
            return ErrorCategory.VALUE
        if "zerodivisionerror" in error_lower or "division by zero" in error_lower:
            return ErrorCategory.MATH
        if "runtimeerror" in error_lower:
            return ErrorCategory.RUNTIME
        if "connectionerror" in error_lower or "timeout" in error_lower:
            return ErrorCategory.NETWORK
        if "database" in error_lower or "sql" in error_lower:
            return ErrorCategory.DATABASE
        if "permission" in error_lower or "access denied" in error_lower:
            return ErrorCategory.SECURITY

        return ErrorCategory.UNKNOWN

    def _analyze_root_cause(self, error_message: str, error_type: str, category: ErrorCategory, context: Dict[str, Any]) -> str:
        """Analyze root cause."""
        if self.ai_router:
            try:
                prompt = f"""Analyze root cause of this error.

Error: {error_message}
Type: {error_type}
Category: {category.value}
Context: {json.dumps(context)[:500]}

Root cause (1-2 sentences):"""
                root_cause = self.ai_router.ask(prompt, task_type="error_analysis")
                return root_cause.strip()
            except Exception:
                pass

        # Fallback root cause
        root_causes = {
            ErrorCategory.IMPORT: "Missing or incorrect import statement",
            ErrorCategory.SYNTAX: "Syntax error in code",
            ErrorCategory.ATTRIBUTE: "Attribute does not exist on object",
            ErrorCategory.NAME: "Variable or function not defined",
            ErrorCategory.TYPE: "Type mismatch in operation",
            ErrorCategory.RUNTIME: "Runtime execution error",
            ErrorCategory.NETWORK: "Network connectivity issue",
        }
        return root_causes.get(category, f"Unknown error: {error_message[:100]}")

    def _determine_severity(self, category: ErrorCategory, error_message: str) -> str:
        """Determine error severity."""
        high_severity = [ErrorCategory.SYNTAX, ErrorCategory.IMPORT, ErrorCategory.DATABASE]
        medium_severity = [ErrorCategory.ATTRIBUTE, ErrorCategory.TYPE, ErrorCategory.RUNTIME]

        if category in high_severity:
            return "high"
        elif category in medium_severity:
            return "medium"
        return "low"

    def propose_fix(self, analysis: ErrorAnalysis, code: str = "") -> Optional[str]:
        """Propose fix for error.

        Args:
            analysis: Error analysis
            code: Source code around error

        Returns:
            Fixed code or None
        """
        # Check knowledge base first
        known_solution = self.kb.lookup(str(analysis.root_cause))
        if known_solution and known_solution.fix_code:
            self.kb.record_outcome(known_solution.solution_id, True)
            return known_solution.fix_code

        # Generate fix using AI
        if self.ai_router and code:
            try:
                prompt = f"""Fix this error in the code.

Error: {analysis.root_cause}
Category: {analysis.category.value}
Code:
{code[:1000]}

Return ONLY the fixed code, no explanations:"""
                fixed_code = self.ai_router.ask(prompt, task_type="error_fix")
                return fixed_code.strip()
            except Exception:
                pass

        return None

    def learn(self, error: Exception, fix_successful: bool, fix_code: str = ""):
        """Learn from error and fix outcome.

        Args:
            error: Original error
            fix_successful: Whether fix worked
            fix_code: Code that fixed the error
        """
        analysis = self.analyze(error)

        if fix_code:
            solution = ErrorSolution(
                solution_id=f"sol_{int(time.time())}",
                error_pattern=str(error)[:200],
                fix_description=f"Fix for {analysis.category.value} error",
                fix_code=fix_code,
                confidence=100.0 if fix_successful else 0.0,
                success_count=1 if fix_successful else 0,
                failure_count=0 if fix_successful else 1,
                created_at=datetime.now().isoformat(),
            )
            self.kb.add_solution(solution)

        self._emit("ERROR_LEARNED", {
            "category": analysis.category.value,
            "fix_successful": fix_successful,
        })

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        categories: Dict[str, int] = {}
        for analysis in self._error_history:
            cat = analysis.category.value
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_errors": len(self._error_history),
            "by_category": categories,
            "knowledge_base": self.kb.get_stats(),
        }

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        """Emit event through event bus."""
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, payload)
            except Exception:
                pass
