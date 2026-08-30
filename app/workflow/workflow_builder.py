from app.workflow.models import Workflow, WorkflowStatus, WorkflowStep
from app.workflow.workflow_validator import WorkflowValidator


class WorkflowBuilder:
    """Selects lifecycle stages based on scope, uncertainty, risk, and deployment intent."""

    def __init__(self, validator=None):
        self.validator = validator or WorkflowValidator()

    def build(self, goal, requirements=None, risk=None, simulation=None):
        requirements = requirements or {}
        features = tuple(requirements.get("features", ()))
        ambiguities = tuple(requirements.get("ambiguities", ()))
        risk_score = (risk or {}).get("score", 0)
        text = goal.casefold()
        needs_research = len(features) >= 3 or bool(ambiguities) or risk_score >= 30
        needs_deployment = any(term in text for term in ("deploy", "deployment", "production", "release"))
        needs_repair = risk_score >= 30 or bool((simulation or {}).get("risks"))

        steps = [WorkflowStep("requirements", "Analyze requirements")]
        architecture_dependencies = ["requirements"]
        if needs_research:
            steps.append(WorkflowStep("research", "Research risks and implementation options", ("requirements",)))
            architecture_dependencies.append("research")
        steps.extend([
            WorkflowStep("architecture", "Design architecture", tuple(architecture_dependencies)),
            WorkflowStep("planning", "Create an execution plan", ("architecture",)),
            WorkflowStep("execution", "Implement the approved plan", ("planning",)),
            WorkflowStep("validation", "Validate implementation", ("execution",)),
            WorkflowStep("testing", "Run automated tests", ("execution",)),
        ])
        documentation_dependencies = ["validation", "testing"]
        if needs_repair:
            steps.append(WorkflowStep(
                "repair", "Repair validation findings", ("validation",), required=False,
                when="repair_required", metadata={"conditional": True},
            ))
            documentation_dependencies.append("repair")
        steps.append(WorkflowStep("documentation", "Generate project documentation", tuple(documentation_dependencies)))
        if needs_deployment:
            steps.append(WorkflowStep("deployment", "Deploy the validated project", ("documentation",)))

        workflow = Workflow(
            goal=goal,
            steps=steps,
            status=WorkflowStatus.READY,
            metadata={
                "needs_research": needs_research,
                "needs_repair": needs_repair,
                "needs_deployment": needs_deployment,
                "feature_count": len(features),
            },
        )
        return self.validator.validate(workflow)
