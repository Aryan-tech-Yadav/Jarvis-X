"""Autonomous Root Cause Diagnostic Engine."""

from __future__ import annotations

import ast
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models.repair_result import RootCauseAnalysis


class RootCauseEngine:
    """Diagnoses test failures and runtime exceptions into actionable root causes."""

    # Traceback extraction patterns
    FILE_LINE_PATTERN = re.compile(r'File "([^"]+)", line (\d+)(?:, in (\w+))?')
    ERROR_LINE_PATTERN = re.compile(r"^([A-Za-z0-9_.]+(?:Error|Exception|Warning)):\s*(.*)$", re.MULTILINE)

    def diagnose(
        self,
        failure_message: str,
        raw_traceback: str = "",
        context_code: Optional[str] = None,
        context_files: Optional[Dict[str, str]] = None,
    ) -> RootCauseAnalysis:
        tb_text = (raw_traceback + "\n" + failure_message).strip()
        target_files, last_line, last_func = self._extract_traceback_locations(tb_text)
        error_type, error_msg = self._extract_error_type_and_msg(failure_message, tb_text)

        category, root_cause, strategy, symbol, confidence = self._classify_and_diagnose(
            error_type, error_msg, tb_text, context_code
        )

        failure_title = f"{error_type}: {error_msg}" if error_type and error_msg else failure_message[:100]

        return RootCauseAnalysis(
            failure=failure_title.strip(),
            root_cause=root_cause,
            confidence=round(confidence, 2),
            repair_strategy=strategy,
            target_files=target_files,
            error_category=category,
            raw_traceback=raw_traceback,
            failing_symbol=symbol,
            suggested_patch=self._generate_suggested_patch_guidance(category, strategy, symbol),
        )

    def _extract_traceback_locations(self, tb_text: str) -> Tuple[List[str], int, str]:
        matches = self.FILE_LINE_PATTERN.findall(tb_text)
        files: List[str] = []
        last_line = 0
        last_func = ""
        for fpath, lno, func in matches:
            if not fpath.startswith("<") and not "unittest" in fpath and not "importlib" in fpath:
                if fpath not in files:
                    files.append(fpath)
                last_line = int(lno)
                last_func = func
        return files, last_line, last_func

    def _extract_error_type_and_msg(self, failure_msg: str, tb_text: str) -> Tuple[str, str]:
        matches = self.ERROR_LINE_PATTERN.findall(tb_text)
        if matches:
            return matches[-1][0], matches[-1][1].strip()
        if ":" in failure_msg:
            parts = failure_msg.split(":", 1)
            return parts[0].strip(), parts[1].strip()
        return "RuntimeError", failure_msg.strip()


    def _classify_and_diagnose(
        self, error_type: str, error_msg: str, tb_text: str, context_code: Optional[str]
    ) -> Tuple[str, str, str, str, float]:
        err_lower = error_type.lower()
        msg_lower = error_msg.lower()

        # 1. ModuleNotFoundError / ImportError
        if "modulenotfounderror" in err_lower or "importerror" in err_lower:
            symbol_match = re.search(r"No module named '([^']+)'|cannot import name '([^']+)'", error_msg)
            symbol = symbol_match.group(1) or symbol_match.group(2) if symbol_match else ""
            if "circular" in msg_lower or "partially initialized" in msg_lower:
                return (
                    "import",
                    f"Circular import dependency involving '{symbol or error_msg}'",
                    "Break dependency cycle by moving shared types/interfaces to a core module or lazy import",
                    symbol,
                    0.98,
                )
            return (
                "import",
                f"Missing module or imported symbol '{symbol or error_msg}'",
                f"Add missing module or correct import path for '{symbol}'",
                symbol,
                0.97,
            )

        # 2. KeyError (Missing Configuration / Dictionary Key)
        if "keyerror" in err_lower:
            key_match = re.search(r"['\"]([^'\"]+)['\"]", error_msg)
            symbol = key_match.group(1) if key_match else error_msg
            if "config" in msg_lower or "settings" in msg_lower or "env" in msg_lower or "host" in msg_lower or "port" in msg_lower:
                return (
                    "config",
                    f"Missing configuration key '{symbol}'",
                    f"Load default configuration or use .get('{symbol}', default_value)",
                    symbol,
                    0.97,
                )
            return (
                "config",
                f"Dictionary key '{symbol}' not found",
                f"Safely access key with dict.get('{symbol}') or provide default initialization",
                symbol,
                0.95,
            )

        # 3. AttributeError (Missing method / property / NoneType)
        if "attributeerror" in err_lower:
            attr_match = re.search(r"object has no attribute '([^']+)'|'NoneType' object has no attribute '([^']+)'", error_msg)
            symbol = attr_match.group(1) or attr_match.group(2) if attr_match else ""
            if "'NoneType'" in error_msg:
                return (
                    "attribute",
                    f"Variable is None when attempting to access attribute '{symbol}'",
                    f"Add null check 'if obj is not None:' before accessing '{symbol}'",
                    symbol,
                    0.96,
                )
            return (
                "attribute",
                f"Object missing required attribute or method '{symbol}'",
                f"Define attribute '{symbol}' in class __init__ or implement missing method",
                symbol,
                0.95,
            )

        # 4. NameError (Undefined Variable / Function)
        if "nameerror" in err_lower:
            name_match = re.search(r"name '([^']+)' is not defined", error_msg)
            symbol = name_match.group(1) if name_match else ""
            return (
                "name",
                f"Reference to undefined symbol '{symbol}'",
                f"Define variable or import '{symbol}' before usage",
                symbol,
                0.97,
            )

        # 5. TypeError
        if "typeerror" in err_lower:
            if "missing" in msg_lower and "positional argument" in msg_lower:
                arg_match = re.search(r"missing \d+ required positional argument[s]?: '([^']+)'", error_msg)
                symbol = arg_match.group(1) if arg_match else ""
                return (
                    "type",
                    f"Function call missing required positional argument '{symbol}'",
                    f"Supply required argument '{symbol}' or provide default value in parameter list",
                    symbol,
                    0.95,
                )
            if "unsupported operand" in msg_lower or "'NoneType'" in msg_lower:
                return (
                    "type",
                    f"Type mismatch or invalid operation: {error_msg}",
                    "Validate variable types before arithmetic/concatenation operations",
                    "",
                    0.92,
                )
            return (
                "type",
                f"Type error: {error_msg}",
                "Ensure argument types and return values match expected signatures",
                "",
                0.90,
            )

        # 6. SyntaxError / IndentationError
        if "syntaxerror" in err_lower or "indentationerror" in err_lower:
            return (
                "syntax",
                f"Invalid syntax or indentation: {error_msg}",
                "Correct unbalanced syntax, missing colon, or improper indentation",
                "",
                0.99,
            )

        # 7. AssertionError
        if "assertionerror" in err_lower:
            return (
                "assertion",
                f"Test assertion failed: {error_msg or 'Expected condition evaluated to False'}",
                "Adjust function logic to satisfy expected test assertion condition",
                "",
                0.93,
            )

        # 8. ZeroDivisionError
        if "zerodivisionerror" in err_lower:
            return (
                "math",
                "Division by zero encountered",
                "Add guard condition check before division (e.g. if denominator != 0)",
                "",
                0.98,
            )

        # 9. RecursionError
        if "recursionerror" in err_lower:
            return (
                "recursion",
                "Maximum recursion depth exceeded in recursive call",
                "Add or correct base termination condition in recursive function",
                "",
                0.96,
            )

        # Default Generic Diagnosis
        return (
            "runtime",
            f"Runtime exception: {error_msg or error_type}",
            "Add defensive exception handling or validate pre-conditions",
            "",
            0.85,
        )

    def _generate_suggested_patch_guidance(self, category: str, strategy: str, symbol: str) -> str:
        if category == "config" and symbol:
            return f"config.get('{symbol}', default_value)"
        if category == "import" and symbol:
            return f"from {symbol} import {symbol}"
        if category == "attribute" and symbol:
            return f"self.{symbol} = default_value"
        if category == "name" and symbol:
            return f"{symbol} = None"
        return strategy
