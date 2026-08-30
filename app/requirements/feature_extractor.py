class FeatureExtractor:
    """Extract common product capabilities without requiring an LLM call."""

    FEATURE_KEYWORDS = {
        "authentication": ("auth", "login", "sign in", "signup", "register", "account"),
        "profiles": ("profile", "user page"),
        "posts": ("post", "feed", "publish", "blog"),
        "comments": ("comment", "reply"),
        "search": ("search", "discover", "find"),
        "notifications": ("notification", "alert"),
        "payments": ("payment", "checkout", "subscription", "cart", "e-commerce", "ecommerce"),
        "uploads": ("upload", "image", "photo", "video", "file"),
        "realtime": ("chat", "real-time", "realtime", "live"),
        "admin": ("admin", "moderation", "dashboard"),
    }

    PRODUCT_DEFAULTS = {
        "calculator": ("core",),
        "todo": ("core",),
        "notes": ("core",),
        "crm": ("core",),
        "school": ("core",),
        "inventory": ("core",),
        "cms": ("core",),
        "hrms": ("core",),
        "hospital": ("core",),
        "banking": ("core",),
        "lms": ("core",),
        "social network": ("core",),
        "ai saas": ("core",),
        "multi-agent": ("core",),
        "vs code": ("core",),
        "file synchronization": ("core",),
        "project management": ("core",),
        "instagram": ("authentication", "profiles", "posts", "comments", "search", "notifications", "uploads"),
        "e-commerce": ("authentication", "payments", "search", "admin"),
        "ecommerce": ("authentication", "payments", "search", "admin"),
        "chat": ("authentication", "realtime", "notifications"),
    }

    def extract(self, text):
        value = str(text or "").casefold()
        found = {name for name, keywords in self.FEATURE_KEYWORDS.items() if any(word in value for word in keywords)}
        for product, defaults in self.PRODUCT_DEFAULTS.items():
            if product in value:
                found.update(defaults)
        return sorted(found)
