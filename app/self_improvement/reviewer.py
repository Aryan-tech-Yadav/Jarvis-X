"""AI Code Reviewer for self-improvement.

Reviews modified files and provides detailed feedback.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.ai.ai_manager import AIManager
from app.core.logger import Logger


CODE_REVIEW_PROMPT = """
You are a senior code reviewer reviewing a code change.

Original file:
{original}

Modified file:
{modified}

Context:
{context}

Provide a detailed review with:
1. pros: list of benefits of this change
2. cons: list of concerns or issues
3. risks: list of potential risks
4. alternatives: alternative approaches
5. security: security considerations
6. performance: performance implications
7. maintainability: maintainability assessment
8. future_issues: potential future issues
9. overall_assessment: one of [APPROVED, APPROVED_WITH_NOTES, NEEDS_REVISION, REJECTED]
10. confidence: 0.0 to 1.0

Return ONLY valid JSON.

Schema:
{{
  "pros": [],
  "cons": [],
  "risks": [],
  "alternatives": [],
  "security": "",
  "performance": "",
  "maintainability": "",
  "future_issues": [],
  "overall_assessment": "APPROVED",
  "confidence": 0.9
}}
"""


@dataclass
class CodeReview:
    """Code review result."""

    file: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    security: str = ""
    performance: str = ""
    maintainability: str = ""
    future_issues: List[str] = field(default_factory=list)
    overall_assessment: str = "NEEDS_REVISION"
    confidence: float = 0.0
    approved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "pros": list(self.pros),
            "cons": list(self.cons),
            "risks": list(self.risks),
            "alternatives": list(self.alternatives),
            "security": self.security,
            "performance": self.performance,
            "maintainability": self.maintainability,
            "future_issues": list(self.future_issues),
            "overall_assessment": self.overall_assessment,
            "confidence": round(self.confidence, 2),
            "approved": self.approved,
        }


class AICodeReviewer:
    """AI-powered code reviewer for self-improvement."""

    def __init__(self, ai=None):
        self.ai = ai or AIManager()

    def review(self, original_content: str, modified_content: str, file_path: str, context: str = "") -> CodeReview:
        """Review a code change."""
        Logger.info(f"[AICodeReviewer] Reviewing: {file_path}")
        
        review = CodeReview(file=file_path)
        
        # Try AI review
        try:
            ai_review = self._ai_review(original_content, modified_content, file_path, context)
            if ai_review:
                review = ai_review
        except Exception as exc:
            Logger.warning(f"[AICodeReviewer] AI review failed: {exc}")
        
        # Fallback to static review
        if not review.pros and not review.cons:
            review = self._static_review(original_content, modified_content, file_path)
        
        # Determine approval
        review.approved = review.overall_assessment in ("APPROVED", "APPROVED_WITH_NOTES")
        
        return review

    def _ai_review(self, original: str, modified: str, file_path: str, context: str) -> Optional[CodeReview]:
        """Use AI to review code change."""
        prompt = CODE_REVIEW_PROMPT.format(
            original=original[:4000],
            modified=modified[:4000],
            context=context[:2000] if context else "Self-improvement change",
        )
        
        response = self.ai.ask(prompt)
        
        # Parse response
        cleaned = response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        import json
        data = json.loads(cleaned)
        
        review = CodeReview(
            file=file_path,
            pros=data.get("pros", []),
            cons=data.get("cons", []),
            risks=data.get("risks", []),
            alternatives=data.get("alternatives", []),
            security=data.get("security", ""),
            performance=data.get("performance", ""),
            maintainability=data.get("maintainability", ""),
            future_issues=data.get("future_issues", []),
            overall_assessment=data.get("overall_assessment", "NEEDS_REVISION"),
            confidence=float(data.get("confidence", 0.5)),
        )
        return review

    def _static_review(self, original: str, modified: str, file_path: str) -> CodeReview:
        """Static analysis fallback review."""
        review = CodeReview(file=file_path)
        
        try:
            original_tree = ast.parse(original)
            modified_tree = ast.parse(modified)
        except SyntaxError as exc:
            review.cons.append(f"Syntax error in modified code: {exc}")
            review.overall_assessment = "REJECTED"
            review.confidence = 1.0
            return review
        
        # Compare complexity
        original_complexity = self._compute_complexity(original_tree)
        modified_complexity = self._compute_complexity(modified_tree)
        
        if modified_complexity > original_complexity:
            review.cons.append(f"Complexity increased from {original_complexity} to {modified_complexity}")
        elif modified_complexity < original_complexity:
            review.pros.append(f"Complexity reduced from {original_complexity} to {modified_complexity}")
        
        # Compare size
        original_lines = len(original.splitlines())
        modified_lines = len(modified.splitlines())
        
        if modified_lines > original_lines * 1.5:
            review.cons.append(f"File size increased significantly: {original_lines} -> {modified_lines} lines")
        elif modified_lines < original_lines * 0.5:
            review.risks.append(f"File size reduced significantly: {original_lines} -> {modified_lines} lines")
        
        # Default assessment
        if not review.cons and not review.risks:
            review.overall_assessment = "APPROVED"
            review.pros.append("No obvious issues detected")
        elif len(review.cons) <= 1 and not review.risks:
            review.overall_assessment = "APPROVED_WITH_NOTES"
        else:
            review.overall_assessment = "NEEDS_REVISION"
        
        review.confidence = 0.6
        return review

    @staticmethod
    def _compute_complexity(tree: ast.AST) -> int:
        """Compute cyclomatic complexity."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
