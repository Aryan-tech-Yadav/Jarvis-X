"""Unit tests for QA Engine and Static Analyzer."""

import tempfile
import unittest
from pathlib import Path

from app.quality.models import IssueSeverity, QualityCategory
from app.quality.qa_engine import QAEngine, StaticAnalyzer


class TestQAEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_static_analyzer_detects_complexity_and_smells(self):
        code = """def complex_function(a, b, c, d, e, f, g):
    if a:
        if b:
            for x in range(10):
                if c and d or e:
                    return x
    elif f:
        while g:
            pass
    return None
"""
        src = self.root / "complex_module.py"
        src.write_text(code, encoding="utf-8")

        analyzer = StaticAnalyzer(str(self.root))
        result = analyzer.scan_directory(str(self.root))

        self.assertIn(result.complexity_level, ["Medium", "High"])
        self.assertTrue(any(i.rule == "too_many_arguments" for i in result.issues))

    def test_static_analyzer_detects_circular_imports(self):
        mod_a = self.root / "mod_a.py"
        mod_b = self.root / "mod_b.py"

        mod_a.write_text("import mod_b\ndef func_a(): pass\n", encoding="utf-8")
        mod_b.write_text("import mod_a\ndef func_b(): pass\n", encoding="utf-8")

        analyzer = StaticAnalyzer(str(self.root))
        result = analyzer.scan_directory(str(self.root))

        self.assertTrue(len(result.circular_imports) > 0 or any(i.rule == "circular_import" for i in result.issues))

    def test_static_analyzer_detects_unused_variables_and_dead_functions(self):
        code = """def my_function():
    unused_val = 42
    result = 100
    return result

def _uncalled_private_helper():
    return 123
"""
        src = self.root / "helper.py"
        src.write_text(code, encoding="utf-8")

        analyzer = StaticAnalyzer(str(self.root))
        result = analyzer.scan_directory(str(self.root))

        self.assertTrue(any(uv["name"] == "unused_val" for uv in result.unused_variables))
        self.assertTrue(any(df["name"] == "_uncalled_private_helper" for df in result.dead_functions))

    def test_qa_engine_architecture_layer_violation(self):
        models_dir = self.root / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        bad_model = models_dir / "user_model.py"
        bad_model.write_text("import controllers.auth_controller\nclass User: pass\n", encoding="utf-8")

        qa = QAEngine(str(self.root))
        issues = qa.check_architecture_rules(str(self.root))

        self.assertTrue(any(i.rule == "architecture_layer_violation" for i in issues))

    def test_qa_engine_naming_rules(self):
        code = """class bad_named_class:
    pass

def BadNamedFunction():
    return 1
"""
        src = self.root / "naming.py"
        src.write_text(code, encoding="utf-8")

        qa = QAEngine(str(self.root))
        issues = qa.check_naming_rules(str(self.root))

        self.assertTrue(any(i.rule == "naming_class_pascal_case" for i in issues))
        self.assertTrue(any(i.rule == "naming_function_snake_case" for i in issues))

    def test_qa_engine_full_evaluation(self):
        code = '''"""Sample module."""

class Calculator:
    """Calculates sums."""

    def add(self, a: int, b: int) -> int:
        """Adds two numbers."""
        return a + b
'''
        (self.root / "calc.py").write_text(code, encoding="utf-8")
        (self.root / "README.md").write_text("# Calc", encoding="utf-8")
        (self.root / "tests").mkdir(parents=True, exist_ok=True)
        (self.root / "tests" / "test_calc.py").write_text("import unittest\n", encoding="utf-8")

        qa = QAEngine(str(self.root))
        score, static_res = qa.evaluate_quality(str(self.root))

        self.assertGreaterEqual(score.overall_score, 85.0)
        self.assertIn(score.grade, ["A+", "A", "B"])
        self.assertIn("architecture", score.category_scores)
        self.assertIn("code_quality", score.category_scores)
        self.assertIn("documentation", score.category_scores)
