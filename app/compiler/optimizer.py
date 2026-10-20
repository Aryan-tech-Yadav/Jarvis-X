"""Deterministic normalization and de-duplication of specifications."""

from .parser import EngineeringSpec


class SpecOptimizer:
    def optimize(self, spec: EngineeringSpec) -> EngineeringSpec:
        spec.project = " ".join(spec.project.split())
        spec.modules = list(dict.fromkeys(" ".join(item.split()) for item in spec.modules))
        spec.roles = list(dict.fromkeys(" ".join(item.split()) for item in spec.roles))
        spec.database = spec.database.strip()
        spec.auth = spec.auth.strip()
        return spec

