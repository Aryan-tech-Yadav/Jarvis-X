"""Domain and project-type detection."""


class DomainDetector:
    DOMAIN_ALIASES = {
        "hospital": "healthcare",
        "clinic": "healthcare",
        "medical": "healthcare",
        "e-commerce": "ecommerce",
        "ecommerce": "ecommerce",
    }

    def detect(self, goal: str, requirements=None) -> str:
        value = goal.casefold()
        for keyword, domain in self.DOMAIN_ALIASES.items():
            if keyword in value:
                return domain
        return getattr(requirements, "domain", "general") if requirements else "general"

    def project_type(self, goal: str, requirements=None) -> str:
        return getattr(requirements, "project_type", "web") if requirements else "web"

