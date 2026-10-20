class Plugin:
    name = "plugin"
    version = "1.0.0"
    description = ""

    def initialize(self):
        return True

    def shutdown(self):
        return True

    def tools(self):
        return []

    def metadata(self):
        return {"name": self.name, "version": self.version, "description": self.description}