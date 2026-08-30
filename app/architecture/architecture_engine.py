from .architecture_patterns import ArchitecturePatterns
from .architecture_validator import ArchitectureValidator
from .module_mapper import ModuleMapper
from .scalability_checker import ScalabilityChecker
from .technology_selector import TechnologySelector


class ArchitectureEngine:
    def __init__(self, patterns=None, technology_selector=None, module_mapper=None,
                 scalability_checker=None, validator=None):
        self.patterns = patterns or ArchitecturePatterns()
        self.technology_selector = technology_selector or TechnologySelector()
        self.module_mapper = module_mapper or ModuleMapper()
        self.scalability_checker = scalability_checker or ScalabilityChecker()
        self.validator = validator or ArchitectureValidator()

    def design(self, requirements):
        plan = {
            "requirements": requirements,
            "pattern": self.patterns.choose(requirements),
            "technology": self.technology_selector.select(requirements),
            "modules": self.module_mapper.map(requirements),
        }
        plan["scalability_warnings"] = self.scalability_checker.check(plan)
        plan.update(self.validator.validate(plan))
        plan["rationale"] = "Selected {pattern} for {count} identified capabilities.".format(
            pattern=plan["pattern"], count=len(requirements.get("features", ()))
        )
        return plan
