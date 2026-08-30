"""Tests for architecture_designer.py."""

import pytest

from app.engineering.architecture_designer import ArchitectureDesigner, SystemArchitecture


class TestArchitectureDesigner:
    def setup_method(self):
        self.designer = ArchitectureDesigner()

    def _make_analysis(self, project_type='web', backend='FastAPI', frontend='React', database='PostgreSQL', **kwargs):
        defaults = {
            'project_type': project_type,
            'backend': backend,
            'frontend': frontend,
            'database': database,
            'cache': 'Redis',
            'queue': None,
            'storage': None,
            'monitoring': 'Prometheus',
        }
        defaults.update(kwargs)
        return type('obj', (object,), defaults)()

    def test_design_web_architecture(self):
        analysis = self._make_analysis()
        arch = self.designer.design("Build web app", analysis)
        assert isinstance(arch, SystemArchitecture)
        assert len(arch.layers) > 0
        assert len(arch.components) > 0

    def test_design_api_architecture(self):
        analysis = self._make_analysis(project_type='api', frontend=None)
        arch = self.designer.design("Build API", analysis)
        assert len(arch.layers) > 0

    def test_tech_stack_populated(self):
        analysis = self._make_analysis()
        arch = self.designer.design("Build web app", analysis)
        assert arch.tech_stack['backend'] == 'FastAPI'
        assert arch.tech_stack['frontend'] == 'React'

    def test_mermaid_diagram_generated(self):
        analysis = self._make_analysis()
        arch = self.designer.design("Build web app", analysis)
        assert 'graph TD' in arch.mermaid_diagram
        assert len(arch.mermaid_diagram.split('\n')) > 2

    def test_to_dict(self):
        analysis = self._make_analysis()
        arch = self.designer.design("Build web app", analysis)
        data = arch.to_dict()
        assert 'layers' in data
        assert 'components' in data
        assert 'mermaid_diagram' in data
