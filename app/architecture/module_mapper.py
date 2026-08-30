class ModuleMapper:
    def map(self, requirements):
        features = requirements.get("features", ())
        modules = {"api": ["health", "configuration"], "tests": ["unit", "integration"]}
        for feature in features:
            modules[feature] = ["models", "service", "routes", "tests"]
        return modules
