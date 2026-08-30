"""Architecture design facade."""

from app.engineering.architecture_designer import ArchitectureDesigner as EngineeringArchitectureDesigner


class ArchitectureDesigner:
    def __init__(self, designer=None):
        self.designer = designer or EngineeringArchitectureDesigner()

    def design(self, requirements):
        return self.designer.design(requirements.raw_requirement, requirements.analysis)

