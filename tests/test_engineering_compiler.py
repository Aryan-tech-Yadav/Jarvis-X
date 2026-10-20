import unittest

from app.compiler import DSLGenerator, DSLParser, SemanticError


class TestEngineeringCompiler(unittest.TestCase):
    SOURCE = """PROJECT CRM
MODULE Customer
MODULE Sales
ROLE Admin
DATABASE PostgreSQL
AUTH JWT
"""

    def test_compiles_dsl_to_workflow(self):
        result = DSLGenerator().compile(self.SOURCE)
        self.assertEqual(result["specification"]["project"], "CRM")
        self.assertEqual(result["workflow"]["steps"][1]["depends_on"], ["requirements"])
        self.assertEqual(result["workflow"]["steps"][2]["modules"], ["Customer", "Sales"])

    def test_semantic_validation_rejects_unknown_database(self):
        with self.assertRaises(SemanticError):
            DSLGenerator().compile("PROJECT Demo\nMODULE Core\nDATABASE Oracle")

    def test_parser_requires_project(self):
        with self.assertRaises(ValueError):
            DSLParser().parse("MODULE Core")


if __name__ == "__main__":
    unittest.main()
