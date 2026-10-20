import json

import pytest

from app.project.reconnaissance import ProjectReconnaissance


class FakeAI:
    def __init__(self, response):
        self.response = response

    def ask(self, prompt):
        return self.response


def valid_result():
    return {
        "project_summary": "A demo app",
        "target_users": ["Students"],
        "screens": [],
        "user_flows": [],
        "entities": [],
        "features": [
            {
                "feature": "Sign in",
                "area": "Auth",
                "priority": "must",
                "evidence": "Project brief",
            }
        ],
        "out_of_scope": [],
        "risks": [],
        "estimated_size": "M",
        "next_steps": ["Build the sign-in flow"],
    }


def test_analyze_parses_json_and_sets_feature_status():
    ai = FakeAI("```json\n" + json.dumps(valid_result()) + "\n```")
    result = ProjectReconnaissance(ai=ai).analyze("Build a demo app")
    assert result["features"][0]["priority"] == "must"
    assert result["features"][0]["implementation_status"] == "not_started"


def test_empty_brief_is_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        ProjectReconnaissance(ai=FakeAI("{}")).analyze(" ")


def test_invalid_json_is_rejected():
    with pytest.raises(ValueError, match="invalid JSON"):
        ProjectReconnaissance(ai=FakeAI("{invalid json")).analyze("Build an app")


def test_missing_schema_fields_are_rejected():
    with pytest.raises(ValueError, match="missing fields"):
        ProjectReconnaissance(ai=FakeAI('{"project_summary": "demo"}')).analyze(
            "Build an app"
        )


def test_invalid_feature_priority_is_rejected():
    result = valid_result()
    result["features"][0]["priority"] = "urgent"
    with pytest.raises(ValueError, match="invalid priority"):
        ProjectReconnaissance(ai=FakeAI(json.dumps(result))).analyze("Build an app")


def test_markdown_contains_feature_matrix():
    markdown = ProjectReconnaissance.render_markdown(valid_result())
    assert "## Feature matrix" in markdown
    assert "Sign in" in markdown
    assert "Build the sign-in flow" in markdown


def test_update_feature_status():
    result = valid_result()
    ProjectReconnaissance.update_feature_status(
        result, "Sign in", "in_progress"
    )
    assert result["features"][0]["implementation_status"] == "in_progress"


def test_update_unknown_feature_fails():
    with pytest.raises(ValueError, match="Feature not found"):
        ProjectReconnaissance.update_feature_status(
            valid_result(), "Unknown feature", "completed"
        )


def test_invalid_feature_status_fails():
    with pytest.raises(ValueError, match="Invalid status"):
        ProjectReconnaissance.update_feature_status(
            valid_result(), "Sign in", "almost_done"
        )


def test_save_json_and_markdown(tmp_path):
    result = valid_result()
    json_path = ProjectReconnaissance.save_json(
        result, str(tmp_path / "reports" / "recon.json")
    )
    md_path = ProjectReconnaissance.save_markdown(
        result, str(tmp_path / "reports" / "recon.md")
    )

    saved = json.loads(open(json_path, encoding="utf-8").read())
    markdown = open(md_path, encoding="utf-8").read()

    assert saved["features"][0]["feature"] == "Sign in"
    assert "## Feature matrix" in markdown
