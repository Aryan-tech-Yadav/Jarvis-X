from unittest.mock import patch

from app.project.project_planner import ProjectPlanner


VALID_PLAN = {
    "project_name": "demo_app",
    "folders": ["app"],
    "files": [
        {"name": "main.py", "type": "python"}
    ],
}

INVALID_JSON = (
    '{"project_name":"demo_app",'
    '"folders":[],"files":[],}'
)


class FakeAI:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def ask(self, prompt, **kwargs):
        self.calls.append(prompt)
        if not self.responses:
            raise AssertionError("Unexpected extra AI call")
        return self.responses.pop(0)


class FakeAdapter:
    def prepare_prompt(self, brief):
        return f"RECON BLUEPRINT\n{brief}", {"project_summary": "Demo"}


def test_invalid_json_retries_and_returns_valid_plan():
    import json

    ai = FakeAI([INVALID_JSON, json.dumps(VALID_PLAN)])

    with patch("app.project.project_planner.AIManager", return_value=ai):
        planner = ProjectPlanner(
            use_reconnaissance=True,
            reconnaissance_adapter=FakeAdapter(),
        )
        result = planner.plan("Create a demo app")

    assert result == VALID_PLAN
    assert len(ai.calls) == 2
    assert "Original planning request" in ai.calls[1]


def test_invalid_json_after_retry_returns_none_without_crashing():
    ai = FakeAI([INVALID_JSON, INVALID_JSON])

    with patch("app.project.project_planner.AIManager", return_value=ai):
        planner = ProjectPlanner(
            use_reconnaissance=True,
            reconnaissance_adapter=FakeAdapter(),
        )
        result = planner.plan("Create a demo app")

    assert result is None
    assert len(ai.calls) == 2


def test_default_planner_does_not_retry_invalid_json():
    ai = FakeAI([INVALID_JSON])

    with patch("app.project.project_planner.AIManager", return_value=ai):
        planner = ProjectPlanner()
        result = planner.plan("Create a demo app")

    assert result is None
    assert len(ai.calls) == 1
