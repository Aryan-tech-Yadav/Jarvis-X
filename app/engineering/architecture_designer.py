"""Architecture designer for engineering workflow.

Designs system architecture based on analyzed requirements,
producing layered architecture diagrams, component specifications,
and technology mappings.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ArchitectureComponent:
    """A system architecture component."""

    name: str
    layer: str
    technology: Optional[str] = None
    purpose: str = ""
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "layer": self.layer,
            "technology": self.technology,
            "purpose": self.purpose,
            "dependencies": list(self.dependencies),
        }


@dataclass
class SystemArchitecture:
    """Complete system architecture design."""

    name: str
    layers: List[str] = field(default_factory=list)
    components: List[ArchitectureComponent] = field(default_factory=list)
    data_flow: List[str] = field(default_factory=list)
    tech_stack: dict = field(default_factory=dict)
    mermaid_diagram: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "layers": list(self.layers),
            "components": [c.to_dict() for c in self.components],
            "data_flow": list(self.data_flow),
            "tech_stack": dict(self.tech_stack),
            "mermaid_diagram": self.mermaid_diagram,
        }


class ArchitectureDesigner:
    """Design system architecture from requirements.

    Creates layered architecture with components, data flow,
    and technology mapping.
    """

    # Standard architecture layers
    LAYERS = [
        "Client",
        "API Gateway",
        "Load Balancer",
        "Frontend",
        "Backend Services",
        "Cache",
        "Message Queue",
        "Database",
        "Object Storage",
        "Monitoring",
    ]

    # Component templates by layer
    COMPONENT_TEMPLATES = {
        "Client": ["Web App", "Mobile App", "CLI"],
        "API Gateway": ["Kong", "AWS API Gateway", "Custom Gateway"],
        "Load Balancer": ["Nginx", "HAProxy", "AWS ALB"],
        "Frontend": ["React", "Vue", "Angular", "Flutter"],
        "Backend Services": ["FastAPI", "Django", "Flask", "Express"],
        "Cache": ["Redis", "Memcached"],
        "Message Queue": ["Celery", "RabbitMQ", "Kafka"],
        "Database": ["PostgreSQL", "MySQL", "MongoDB"],
        "Object Storage": ["S3", "MinIO", "Azure Blob"],
        "Monitoring": ["Prometheus", "Grafana", "ELK Stack"],
    }

    def design(self, requirement: str, analysis) -> SystemArchitecture:
        """Design system architecture.

        Args:
            requirement: Original requirement string.
            analysis: RequirementAnalysis from analyzer.

        Returns:
            SystemArchitecture with complete design.
        """
        arch = SystemArchitecture(name=requirement[:50])

        # Determine relevant layers based on project type
        arch.layers = self._select_layers(analysis.project_type)

        # Create components for each layer
        arch.components = self._create_components(analysis)

        # Build tech stack
        arch.tech_stack = self._build_tech_stack(analysis)

        # Define data flow
        arch.data_flow = self._define_data_flow(arch.components)

        # Generate Mermaid diagram
        arch.mermaid_diagram = self._generate_mermaid(arch)

        return arch

    def _select_layers(self, project_type: str) -> List[str]:
        """Select relevant architecture layers."""
        if project_type == "web":
            return ["Client", "Load Balancer", "Frontend", "Backend Services", "Database", "Cache", "Monitoring"]
        elif project_type == "api":
            return ["API Gateway", "Load Balancer", "Backend Services", "Cache", "Database", "Queue", "Monitoring"]
        elif project_type == "mobile":
            return ["Mobile App", "API Gateway", "Backend Services", "Database", "Storage", "Cache"]
        elif project_type == "cli":
            return ["CLI", "Backend", "Database"]
        elif project_type == "desktop":
            return ["Desktop App", "Backend", "Database"]
        elif project_type == "game":
            return ["Game Loop", "Input", "Rendering", "Game State", "Audio"]
        else:
            return ["Client", "Backend Services", "Database", "Monitoring"]

    def _create_components(self, analysis) -> List[ArchitectureComponent]:
        """Create components for each layer."""
        components = []
        for layer in self._select_layers(analysis.project_type):
            templates = self.COMPONENT_TEMPLATES.get(layer, [])
            if templates:
                # Pick best matching template
                tech = self._match_technology(templates, analysis)
                components.append(ArchitectureComponent(
                    name=layer,
                    layer=layer,
                    technology=tech,
                    purpose=f"{layer} layer of the system",
                    dependencies=[l for l in self._select_layers(analysis.project_type) if l != layer and self._select_layers(analysis.project_type).index(l) > self._select_layers(analysis.project_type).index(layer)],
                ))
        return components

    def _match_technology(self, templates: List[str], analysis) -> Optional[str]:
        """Match best technology from templates based on analysis."""
        tech_stack = {
            "backend": analysis.backend,
            "frontend": analysis.frontend,
            "database": analysis.database,
            "cache": analysis.cache,
            "queue": analysis.queue,
            "storage": analysis.storage,
            "monitoring": analysis.monitoring,
        }
        for template in templates:
            for tech in tech_stack.values():
                if tech and template.lower() in tech.lower():
                    return template
        return templates[0] if templates else None

    def _build_tech_stack(self, analysis) -> dict:
        """Build complete tech stack dictionary."""
        return {
            "backend": analysis.backend,
            "frontend": analysis.frontend,
            "database": analysis.database,
            "cache": analysis.cache,
            "queue": analysis.queue,
            "storage": analysis.storage,
            "monitoring": analysis.monitoring,
        }

    def _define_data_flow(self, components: List[ArchitectureComponent]) -> List[str]:
        """Define data flow between components."""
        flow = []
        for i, comp in enumerate(components):
            if i > 0:
                flow.append(f"{components[i-1].name} -> {comp.name}")
        return flow

    def _generate_mermaid(self, arch: SystemArchitecture) -> str:
        """Generate Mermaid architecture diagram."""
        lines = ["graph TD"]
        for i, comp in enumerate(arch.components):
            safe_name = comp.name.replace(" ", "_").replace("-", "_")
            tech = comp.technology or "Unknown"
            lines.append(f"  {safe_name}[{comp.name}<br/>({tech})]")
            if i > 0:
                prev = arch.components[i-1].name.replace(" ", "_").replace("-", "_")
                lines.append(f"  {prev} --> {safe_name}")
        return "\n".join(lines)
