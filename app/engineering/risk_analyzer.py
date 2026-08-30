"""Risk analyzer for engineering workflow.

Identifies potential risks in a project based on:
  - requirements
  - architecture
  - technology choices
  - domain-specific concerns

Outputs:
  - risk categories
  - risk levels
  - mitigation strategies
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RiskItem:
    """Single identified risk."""

    category: str = ""
    risk: str = ""
    level: str = "medium"  # low, medium, high, critical
    probability: float = 0.0
    impact: float = 0.0
    mitigation: str = ""
    affected_components: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "risk": self.risk,
            "level": self.level,
            "probability": round(self.probability, 2),
            "impact": round(self.impact, 2),
            "mitigation": self.mitigation,
            "affected_components": list(self.affected_components),
        }


@dataclass
class RiskReport:
    """Complete risk analysis report."""

    project_name: str
    overall_risk_level: str = "low"
    risk_score: float = 0.0
    risks: List[RiskItem] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "overall_risk_level": self.overall_risk_level,
            "risk_score": round(self.risk_score, 1),
            "risks": [r.to_dict() for r in self.risks],
            "recommendations": list(self.recommendations),
        }


class RiskAnalyzer:
    """Analyze project risks based on requirements and architecture.

    Identifies security, performance, scalability, and operational risks.
    """

    HIGH_RISK_FEATURES = {
        "authentication": {"category": "security", "level": "high", "probability": 0.7, "impact": 0.9},
        "payment": {"category": "security", "level": "critical", "probability": 0.6, "impact": 0.95},
        "real-time": {"category": "performance", "level": "high", "probability": 0.5, "impact": 0.8},
        "file upload": {"category": "security", "level": "medium", "probability": 0.4, "impact": 0.6},
        "ai": {"category": "complexity", "level": "high", "probability": 0.5, "impact": 0.8},
        "blockchain": {"category": "complexity", "level": "high", "probability": 0.4, "impact": 0.7},
        "iot": {"category": "operational", "level": "medium", "probability": 0.3, "impact": 0.6},
        "mobile": {"category": "compatibility", "level": "medium", "probability": 0.3, "impact": 0.5},
    }

    MITIGATIONS = {
        "authentication": "Use established auth libraries (OAuth2, JWT), implement rate limiting, add 2FA",
        "payment": "Use Stripe/PayPal SDKs, never store card data, implement PCI compliance",
        "real-time": "Use WebSockets with fallback, implement connection pooling, add circuit breakers",
        "file upload": "Validate file types, scan for malware, store outside web root, limit file sizes",
        "ai": "Start with pre-trained models, implement model versioning, monitor inference latency",
        "blockchain": "Use established libraries, implement proper key management, audit smart contracts",
        "iot": "Implement device authentication, use MQTT with TLS, add device heartbeat monitoring",
        "mobile": "Test on multiple devices, implement offline mode, use responsive design",
    }

    def analyze(self, requirement_analysis: Dict, architecture: Optional[Dict] = None) -> RiskReport:
        """Analyze risks based on requirements and architecture."""
        project_name = requirement_analysis.get("project_name", "Unknown")
        features = requirement_analysis.get("features", [])
        domain = requirement_analysis.get("domain", "general")
        keywords = requirement_analysis.get("keywords", [])

        risks = []
        feature_text = " ".join(features + keywords).lower()

        for feature, risk_config in self.HIGH_RISK_FEATURES.items():
            if feature in feature_text or any(trigger in feature_text for trigger in [feature]):
                risk = RiskItem(
                    category=risk_config["category"],
                    risk=f"{feature.title()} implementation complexity",
                    level=risk_config["level"],
                    probability=risk_config["probability"],
                    impact=risk_config["impact"],
                    mitigation=self.MITIGATIONS.get(feature, "Add comprehensive testing and monitoring"),
                    affected_components=self._affected_components(feature, requirement_analysis),
                )
                risks.append(risk)

        # Calculate overall risk
        if risks:
            avg_score = sum(r.probability * r.impact for r in risks) / len(risks)
            high_risk_count = sum(1 for r in risks if r.level in ("high", "critical"))
            overall_level = "critical" if high_risk_count >= 2 else "high" if high_risk_count == 1 else "medium"
        else:
            avg_score = 0.2
            overall_level = "low"

        recommendations = self._generate_recommendations(risks, requirement_analysis)

        return RiskReport(
            project_name=project_name,
            overall_risk_level=overall_level,
            risk_score=avg_score * 100,
            risks=risks,
            recommendations=recommendations,
        )

    def _affected_components(self, feature: str, analysis: Dict) -> List[str]:
        """Determine which components are affected by a risk."""
        modules = analysis.get("modules", [])
        component_map = {
            "authentication": ["auth_service", "user_model", "api_gateway"],
            "payment": ["payment_service", "order_model", "webhook_handler"],
            "real-time": ["websocket_server", "message_queue", "notification_service"],
            "file upload": ["storage_service", "file_validator", "api_endpoints"],
            "ai": ["ml_service", "model_trainer", "inference_api"],
            "blockchain": ["smart_contracts", "wallet_service", "transaction_log"],
            "iot": ["device_manager", "data_ingestion", "telemetry_service"],
            "mobile": ["mobile_api", "push_notifications", "offline_sync"],
        }
        return component_map.get(feature, modules if modules else ["core"])

    def _generate_recommendations(self, risks: List[RiskItem], analysis: Dict) -> List[str]:
        """Generate recommendations based on identified risks."""
        recommendations = []

        if any(r.category == "security" for r in risks):
            recommendations.append("Implement security testing in CI/CD pipeline")
            recommendations.append("Conduct security audit before production deployment")

        if any(r.category == "performance" for r in risks):
            recommendations.append("Add performance benchmarks and load testing")
            recommendations.append("Implement caching strategy early in development")

        if any(r.category == "complexity" for r in risks):
            recommendations.append("Start with MVP scope, iterate based on feedback")
            recommendations.append("Document architecture decisions (ADRs)")

        if not recommendations:
            recommendations.append("Proceed with standard engineering practices")

        return recommendations
