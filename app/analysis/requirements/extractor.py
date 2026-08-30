from app.requirements.feature_extractor import FeatureExtractor

from ..models.requirement_model import RequirementModel


class RequirementExtractor:
    DEFAULT_NON_FUNCTIONAL = ("security", "testing", "logging", "documentation")
    NFR_KEYWORDS = {
        "performance": ("fast", "performance", "latency"),
        "scalability": ("scale", "high traffic", "million"),
        "availability": ("reliable", "uptime", "available"),
        "privacy": ("private", "privacy", "gdpr"),
        "deployment": ("docker", "ci/cd", "deploy", "cloud"),
    }
    DOMAIN_FEATURES = {
        "hospital": ("authentication", "admin", "appointments", "billing", "reports"),
        "restaurant": ("authentication", "orders", "reservations", "admin"),
        "crm": ("authentication", "profiles", "search", "reports", "admin"),
        "school": ("authentication", "profiles", "reports", "admin"),
    }

    def __init__(self, feature_extractor=None):
        self.feature_extractor = feature_extractor or FeatureExtractor()

    def extract(self, goal, existing=None):
        existing = existing or {}
        functional = list(existing.get("features") or self.feature_extractor.extract(goal))
        value = str(goal or "").casefold()
        for product, features in self.DOMAIN_FEATURES.items():
            if product in value:
                functional.extend(features)
        non_functional = set(self.DEFAULT_NON_FUNCTIONAL)
        for name, keywords in self.NFR_KEYWORDS.items():
            if any(keyword in value for keyword in keywords):
                non_functional.add(name)
        return RequirementModel(functional=sorted(set(functional)), non_functional=sorted(non_functional),
                                constraints=list(existing.get("constraints", ())))
