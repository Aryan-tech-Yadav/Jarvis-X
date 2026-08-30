"""Benchmark comparator for self-improvement.

Compares before/after benchmarks and generates actionable insights.
"""

from __future__ import annotations

from typing import Any, Dict, List


class BenchmarkComparator:
    """Compare benchmark results and generate insights."""

    def compare(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two benchmark results."""
        comparison = {
            "before": before,
            "after": after,
            "improvements": [],
            "regressions": [],
            "neutral": [],
            "overall_change": 0.0,
            "recommendation": "",
        }
        
        # Quality score change
        before_score = before.get("quality_score", 0)
        after_score = after.get("quality_score", 0)
        quality_change = after_score - before_score
        comparison["overall_change"] = round(quality_change, 2)
        
        # Compare metrics
        metrics_to_compare = [
            ("quality_score", "Quality Score", True),
            ("complexity_score", "Complexity Score", True),
            ("issues_count", "Issues Count", False),
            ("critical_issues", "Critical Issues", False),
            ("high_issues", "High Issues", False),
            ("medium_issues", "Medium Issues", False),
            ("low_issues", "Low Issues", False),
            ("total_lines", "Total Lines", True),
            ("test_coverage", "Test Coverage", True),
        ]
        
        for key, label, higher_is_better in metrics_to_compare:
            before_val = before.get(key, 0)
            after_val = after.get(key, 0)
            change = after_val - before_val
            
            if higher_is_better:
                if change > 0:
                    comparison["improvements"].append(f"{label}: {before_val} -> {after_val} (+{change})")
                elif change < 0:
                    comparison["regressions"].append(f"{label}: {before_val} -> {after_val} ({change})")
                else:
                    comparison["neutral"].append(f"{label}: unchanged ({before_val})")
            else:
                if change < 0:
                    comparison["improvements"].append(f"{label}: {before_val} -> {after_val} ({change})")
                elif change > 0:
                    comparison["regressions"].append(f"{label}: {before_val} -> {after_val} (+{change})")
                else:
                    comparison["neutral"].append(f"{label}: unchanged ({before_val})")
        
        # Recommendation
        if quality_change > 5:
            comparison["recommendation"] = "STRONG_ACCEPT"
        elif quality_change > 0:
            comparison["recommendation"] = "ACCEPT"
        elif quality_change > -5:
            comparison["recommendation"] = "REVIEW"
        else:
            comparison["recommendation"] = "REJECT"
        
        return comparison
