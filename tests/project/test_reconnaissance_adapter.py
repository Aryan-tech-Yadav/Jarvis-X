import json

from app.project.reconnaissance_adapter import ReconnaissanceAdapter


class FakeReconnaissance:
    def analyze(self, brief):
        assert brief == "Build a hospital management app"
        return {
            "project_summary": "Hospital management",
            "target_users": ["doctor", "patient"],
            "screens": [{"id": "S01", "name": "Dashboard"}],
            "user_flows": [],
            "entities": [],
            "features": [
                {
                    "feature": "Patient registration",
                    "priority": "must",
                    "implementation_status": "not_started",
                }
            ],
            "out_of_scope": [],
            "risks": [],
            "estimated_size": "L",
            "next_steps": ["Design database"],
        }


def test_adapter_preserves_original_brief_and_blueprint():
    adapter = ReconnaissanceAdapter(FakeReconnaissance())

    prompt, blueprint = adapter.prepare_prompt(
        "Build a hospital management app"
    )

    assert "Build a hospital management app" in prompt
    assert "project_name" in prompt
    assert "folders" in prompt
    assert "files" in prompt
    assert blueprint["project_summary"] == "Hospital management"
    assert "Patient registration" in prompt


def test_adapter_includes_valid_json_blueprint():
    adapter = ReconnaissanceAdapter(FakeReconnaissance())

    prompt, _ = adapter.prepare_prompt("Build a hospital management app")
    marker = "Reconnaissance blueprint:\n"
    blueprint_json = prompt.split(marker, 1)[1]
    parsed = json.loads(blueprint_json)

    assert parsed["estimated_size"] == "L"
    assert parsed["target_users"] == ["doctor", "patient"]
