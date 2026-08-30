class BestPractices:
    GUIDANCE = {
        "authentication": ("Use password hashing, short-lived tokens, and authorization tests.", "OWASP Authentication Cheat Sheet"),
        "payments": ("Use a payment provider's hosted flow; never store card data.", "PCI DSS guidance"),
        "uploads": ("Validate type and size, scan uploads, and store objects outside the web root.", "OWASP File Upload Cheat Sheet"),
        "realtime": ("Set connection limits and use a shared broker for horizontally scaled workers.", "WebSocket deployment guidance"),
        "api": ("Version public endpoints and publish an OpenAPI contract.", "OpenAPI Specification"),
    }

    def for_features(self, features):
        return [
            {"topic": feature, "advice": self.GUIDANCE[feature][0], "source": self.GUIDANCE[feature][1]}
            for feature in features if feature in self.GUIDANCE
        ]
