from app.workflow.exceptions import WorkflowValidationError


class WorkflowValidator:
    def validate(self, workflow):
        identifiers = [step.step_id for step in workflow.steps]
        if len(set(identifiers)) != len(identifiers):
            raise WorkflowValidationError("workflow step identifiers must be unique")
        known = set(identifiers)
        for step in workflow.steps:
            missing = set(step.depends_on) - known
            if missing:
                raise WorkflowValidationError(
                    f"step '{step.step_id}' has unknown dependencies: {', '.join(sorted(missing))}"
                )
            if step.step_id in step.depends_on:
                raise WorkflowValidationError(f"step '{step.step_id}' cannot depend on itself")
        self._assert_acyclic(workflow)
        return workflow

    @staticmethod
    def _assert_acyclic(workflow):
        dependencies = {step.step_id: set(step.depends_on) for step in workflow.steps}
        resolved = set()
        while dependencies:
            ready = {identifier for identifier, values in dependencies.items() if values <= resolved}
            if not ready:
                raise WorkflowValidationError("workflow dependencies contain a cycle")
            resolved.update(ready)
            for identifier in ready:
                del dependencies[identifier]
