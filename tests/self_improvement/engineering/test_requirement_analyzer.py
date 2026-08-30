"""Tests for requirement_analyzer.py."""

import pytest

from app.engineering.requirement_analyzer import RequirementAnalyzer, RequirementAnalysis


class TestRequirementAnalyzer:
    def setup_method(self):
        self.analyzer = RequirementAnalyzer()

    def test_analyze_hospital_system(self):
        req = "Build Hospital Management System with patient records and appointments"
        result = self.analyzer.analyze(req)
        assert result.domain == "hospital"
        assert result.project_type == "web"
        assert len(result.roles) > 0
        assert len(result.modules) > 0
        assert result.confidence > 0

    def test_analyze_ecommerce(self):
        req = "Create ecommerce platform with shopping cart and checkout"
        result = self.analyzer.analyze(req)
        assert result.domain == "ecommerce"

    def test_analyze_api_project(self):
        req = "Build REST API for user management"
        result = self.analyzer.analyze(req)
        assert result.project_type == "api"
        assert result.backend is not None

    def test_missing_information_detection(self):
        req = "Build Hospital Management System"
        result = self.analyzer.analyze(req)
        # Should detect missing auth, deployment, etc.
        assert len(result.missing_information) > 0
        assert "authentication" in result.missing_information or "deployment" in result.missing_information

    def test_to_dict(self):
        req = "Build social media platform"
        result = self.analyzer.analyze(req)
        data = result.to_dict()
        assert "domain" in data
        assert "project_type" in data
        assert "modules" in data
        assert "missing_information" in data

    def test_tech_stack_inference(self):
        req = "Build web application with database"
        result = self.analyzer.analyze(req)
        assert result.backend is not None
        assert result.database is not None
