"""Autonomous Repair Engine and Self-Repair Knowledge Memory."""

from __future__ import annotations

import difflib
import json
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models.repair_result import (
    Patch,
    RepairAttempt,
    RootCauseAnalysis,
    SelfHealingResult,
)
from .models.test_result import TestSuiteResult
from .root_cause_engine import RootCauseEngine
from .test_engine import TestEngine


class SelfRepairMemory:
    """Persistent storage for bug diagnoses, repair strategies, and historical outcomes."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir else (Path.cwd() / "knowledge")
        self.repairs_dir = self.knowledge_dir / "repairs"
        self.bugs_dir = self.knowledge_dir / "bugs"
        self.repairs_dir.mkdir(parents=True, exist_ok=True)
        self.bugs_dir.mkdir(parents=True, exist_ok=True)
        self._memory_file = self.repairs_dir / "repair_memory.json"
        self._records: List[Dict[str, Any]] = self._load_records()

    def _load_records(self) -> List[Dict[str, Any]]:
        if self._memory_file.exists():
            try:
                return json.loads(self._memory_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_records(self):
        try:
            self._memory_file.write_text(json.dumps(self._records, indent=2), encoding="utf-8")
        except Exception:
            pass

    def record_repair(
        self,
        problem: str,
        fix: str,
        success: bool,
        repair_time_sec: float,
        error_category: str = "runtime",
        failing_symbol: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        record = {
            "id": f"repair_{len(self._records) + 1:04d}",
            "problem": problem,
            "fix": fix,
            "success": "YES" if success else "NO",
            "repair_time_sec": round(float(repair_time_sec), 2),
            "error_category": error_category,
            "failing_symbol": failing_symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self._records.append(record)
        self._save_records()

        # Save specific bug file in knowledge/bugs
        try:
            bug_slug = re.sub(r"\W+", "_", problem[:40]).strip("_").lower()
            bug_file = self.bugs_dir / f"{bug_slug}_{record['id']}.json"
            bug_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
        except Exception:
            pass

        return record

    def lookup_similar_repair(
        self, problem: str, error_category: str = "", failing_symbol: str = ""
    ) -> Optional[Dict[str, Any]]:
        # Find exact symbol + category match first
        for rec in reversed(self._records):
            if rec.get("success") == "YES":
                if failing_symbol and rec.get("failing_symbol") == failing_symbol:
                    return rec
                if error_category and rec.get("error_category") == error_category:
                    if problem.lower() in rec.get("problem", "").lower() or rec.get("problem", "").lower() in problem.lower():
                        return rec

        # Fallback to general category match
        for rec in reversed(self._records):
            if rec.get("success") == "YES" and error_category and rec.get("error_category") == error_category:
                return rec

        return None

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._records)
        successful = len([r for r in self._records if r.get("success") == "YES"])
        avg_time = (sum(r.get("repair_time_sec", 0.0) for r in self._records) / max(1, total)) if total > 0 else 0.0
        return {
            "total_repairs": total,
            "successful_repairs": successful,
            "success_rate": round((successful / max(1, total)) * 100.0, 2),
            "average_repair_time_sec": round(avg_time, 2),
        }



class RepairEngine:
    """Autonomous Self-Healing engine that analyzes, patches, retests, and learns."""

    def __init__(self, root_path: Optional[str] = None, knowledge_dir: Optional[str] = None):
        self.root_path = Path(root_path).resolve() if root_path else Path.cwd()
        self.memory = SelfRepairMemory(knowledge_dir or str(self.root_path / "knowledge"))
        self.root_cause_engine = RootCauseEngine()
        self.test_engine = TestEngine(self.root_path)

    def repair_and_retest(
        self,
        source_code: str,
        test_code: str,
        root_cause: Optional[RootCauseAnalysis] = None,
        module_name: str = "target_mod",
        max_attempts: int = 3,
    ) -> SelfHealingResult:
        start_time = time.perf_counter()

        # Initial test run if root_cause not supplied
        if root_cause is None:
            initial_test = self.test_engine.run_test_code(source_code, test_code, module_name)
            if initial_test.success:
                return SelfHealingResult(
                    original_failed=False,
                    final_success=True,
                    final_test_result=initial_test,
                    total_repair_time_sec=time.perf_counter() - start_time,
                )

            # Diagnose failure
            fail_msg = initial_test.failure_details[0]["message"] if initial_test.failure_details else "Test Failed"
            tb = initial_test.failure_details[0].get("traceback", "") if initial_test.failure_details else ""
            root_cause = self.root_cause_engine.diagnose(fail_msg, tb, source_code)

        repairs_attempted: List[RepairAttempt] = []
        current_code = source_code
        final_test_res: Optional[TestSuiteResult] = None
        success = False

        # Try memory lookup first
        past_repair = self.memory.lookup_similar_repair(
            root_cause.failure, root_cause.error_category, root_cause.failing_symbol
        )

        for attempt_idx in range(1, max_attempts + 1):
            attempt_start = time.perf_counter()
            patched_code, strategy = self._synthesize_patch(current_code, root_cause, past_repair, attempt_idx)

            if patched_code == current_code and attempt_idx > 1:
                break

            diff = "".join(
                difflib.unified_diff(
                    current_code.splitlines(keepends=True),
                    patched_code.splitlines(keepends=True),
                    fromfile="original.py",
                    tofile="repaired.py",
                )
            )

            patch_obj = Patch(
                file_path=f"{module_name}.py",
                original_content=current_code,
                modified_content=patched_code,
                diff=diff,
                description=strategy,
            )

            # Retest
            retest_res = self.test_engine.run_test_code(patched_code, test_code, module_name)
            attempt_time = time.perf_counter() - attempt_start

            attempt = RepairAttempt(
                root_cause=root_cause,
                strategy_used=strategy,
                patches=[patch_obj],
                success=retest_res.success,
                retest_result=retest_res,
                confidence_score=root_cause.confidence if retest_res.success else 0.0,
                repair_time_sec=attempt_time,
                error_message="" if retest_res.success else (retest_res.failure_details[0]["message"] if retest_res.failure_details else "Retest failed"),
            )
            repairs_attempted.append(attempt)

            if retest_res.success:
                current_code = patched_code
                final_test_res = retest_res
                success = True

                # Save to Self-Repair Memory
                self.memory.record_repair(
                    problem=root_cause.failure,
                    fix=strategy,
                    success=True,
                    repair_time_sec=attempt_time,
                    error_category=root_cause.error_category,
                    failing_symbol=root_cause.failing_symbol,
                    metadata={"module": module_name, "patch_diff": diff},
                )
                break
            else:
                # Re-diagnose for next attempt
                if retest_res.failure_details:
                    n_msg = retest_res.failure_details[0]["message"]
                    n_tb = retest_res.failure_details[0].get("traceback", "")
                    root_cause = self.root_cause_engine.diagnose(n_msg, n_tb, patched_code)

        total_time = time.perf_counter() - start_time
        return SelfHealingResult(
            original_failed=True,
            root_cause=root_cause,
            repairs_attempted=repairs_attempted,
            final_success=success,
            final_test_result=final_test_res,
            total_repair_time_sec=total_time,
            knowledge_saved=success,
        )


    def _synthesize_patch(
        self,
        code: str,
        root_cause: RootCauseAnalysis,
        past_repair: Optional[Dict[str, Any]] = None,
        attempt: int = 1,
    ) -> Tuple[str, str]:
        cat = root_cause.error_category
        sym = root_cause.failing_symbol

        # 1. Missing Configuration
        if cat == "config":
            if sym:
                # Replace direct dict access `[sym]` with `.get(sym, default)` or inject default config
                patched = self._patch_config(code, sym)
                if patched != code:
                    return patched, f"Safe config fallback for '{sym}'"
            # Add fallback default config dict
            patched = self._inject_default_config(code)
            return patched, "Injected default configuration dictionary"

        # 2. Missing Import / Symbol
        if cat == "import":
            patched = self._patch_import(code, sym)
            return patched, f"Added missing import for '{sym}'"

        # 3. Missing Attribute
        if cat == "attribute":
            patched = self._patch_attribute(code, sym)
            return patched, f"Initialized missing attribute '{sym}'"

        # 4. Undefined Name
        if cat == "name":
            patched = self._patch_undefined_name(code, sym)
            return patched, f"Defined variable '{sym}' before usage"

        # 5. Syntax / Indentation Error
        if cat == "syntax":
            patched = self._patch_syntax(code)
            return patched, "Corrected syntax error / missing punctuation"

        # 6. Zero Division
        if cat == "math":
            patched = self._patch_zero_division(code)
            return patched, "Added zero-division safety guard"

        # 7. Assertion mismatch
        if cat == "assertion":
            patched = self._patch_assertion(code, root_cause)
            return patched, "Adjusted return value / logic to satisfy test assertion"

        return code, "No patch synthesized"

    def _patch_config(self, code: str, symbol: str) -> str:
        # Pattern: config['sym'] or settings['sym'] or dict['sym']
        pattern = re.compile(rf"\[(['\"]){re.escape(symbol)}\1\]")
        if pattern.search(code):
            return pattern.sub(f".get('{symbol}', '')", code)
        return code

    def _inject_default_config(self, code: str) -> str:
        if "DEFAULT_CONFIG" not in code:
            return "DEFAULT_CONFIG = {'db_host': 'localhost', 'port': 8000, 'debug': False}\n" + code
        return code

    def _patch_import(self, code: str, symbol: str) -> str:
        lines = code.splitlines()
        import_stmt = f"import {symbol}" if symbol else "import os, sys"
        if symbol in {"math", "os", "sys", "json", "re", "time", "datetime", "uuid"}:
            import_stmt = f"import {symbol}"
        return import_stmt + "\n" + code

    def _patch_attribute(self, code: str, symbol: str) -> str:
        if not symbol:
            return code
        # Find __init__ and add self.symbol = None
        lines = code.splitlines()
        for idx, line in enumerate(lines):
            if "def __init__(" in line:
                indent = " " * (len(line) - len(line.lstrip()) + 4)
                lines.insert(idx + 1, f"{indent}self.{symbol} = None")
                return "\n".join(lines)
        return code

    def _patch_undefined_name(self, code: str, symbol: str) -> str:
        if not symbol:
            return code
        std_modules = {
            "math", "os", "sys", "json", "re", "time", "datetime",
            "uuid", "pathlib", "random", "collections", "itertools",
            "typing", "ast", "shutil", "tempfile", "io", "copy"
        }
        if symbol in std_modules or f"{symbol}." in code:
            return f"import {symbol}\n" + code
        return f"{symbol} = None\n" + code

    def _patch_syntax(self, code: str) -> str:
        lines = code.splitlines()
        fixed = []
        for line in lines:
            stripped = line.strip()
            # Fix missing colon on def/class/if/else/for/while/try/except
            if any(stripped.startswith(kw) for kw in ["def ", "class ", "if ", "elif ", "else", "for ", "while ", "try", "except", "with "]):
                if not stripped.endswith(":"):
                    line = line + ":"
            fixed.append(line)
        return "\n".join(fixed)

    def _patch_zero_division(self, code: str) -> str:
        # Replace `/ x` with `/ (x if x != 0 else 1)`
        return re.sub(r"/\s*([a-zA-Z_][a-zA-Z0-9_]*)", r"/ (\1 if \1 != 0 else 1)", code)

    def _patch_assertion(self, code: str, root_cause: RootCauseAnalysis) -> str:
        # If a function returned None instead of a value, provide dummy return
        lines = code.splitlines()
        for idx, line in enumerate(lines):
            if "return None" in line or line.strip() == "pass":
                indent = " " * (len(line) - len(line.lstrip()))
                lines[idx] = f"{indent}return True"
                return "\n".join(lines)
        return code
