"""Semantic validation for engineering specifications."""

from .parser import EngineeringSpec


class SemanticError(ValueError):
    """Raised when a parsed specification is internally inconsistent."""


class SemanticValidator:
    def validate(self, spec: EngineeringSpec) -> EngineeringSpec:
        if not spec.project.strip():
            raise SemanticError("Project name cannot be empty")
        if not spec.modules:
            raise SemanticError("Project requires at least one MODULE")
        if len(set(item.casefold() for item in spec.modules)) != len(spec.modules):
            raise SemanticError("Duplicate MODULE declarations are not allowed")
        if spec.database and spec.database.casefold() not in {
            "postgresql", "postgres", "mysql", "sqlite", "mongodb"
        }:
            raise SemanticError(f"Unsupported database: {spec.database}")
        if spec.auth and spec.auth.casefold() not in {"jwt", "oauth", "session", "none"}:
            raise SemanticError(f"Unsupported auth: {spec.auth}")
        return spec

