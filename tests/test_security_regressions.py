from app.tools.file_tool import FileTool
from app.toolsystem.tool_policy import ToolPolicy


def test_exists_returns_false_for_missing_file(tmp_path):
    result = FileTool().run(
        "exists",
        path="missing.txt",
        workspace=str(tmp_path),
    )

    assert result["success"] is True, result
    assert result["output"] is False


def test_exists_returns_true_for_existing_file(tmp_path):
    (tmp_path / "present.txt").write_text("hello", encoding="utf-8")

    result = FileTool().run(
        "exists",
        path="present.txt",
        workspace=str(tmp_path),
    )

    assert result["success"] is True, result
    assert result["output"] is True


def test_command_policy_rejects_shell_operators():
    policy = ToolPolicy()

    unsafe_commands = [
        "echo hello; whoami",
        "echo hello>output.txt",
        "echo hello >> output.txt",
        "echo hello && whoami",
        "echo hello | cat",
    ]

    for command in unsafe_commands:
        assert policy.is_command_safe(command) is False, command


def test_command_policy_allows_normal_commands():
    policy = ToolPolicy()

    assert policy.is_command_safe("pytest tests/") is True
    assert policy.is_command_safe("python --version") is True
    assert policy.is_command_safe("unknown-command --help") is False
    assert policy.is_command_safe("python -c 'print(1)'") is False


def test_command_policy_allows_operators_inside_quotes():
    policy = ToolPolicy()

    assert policy.is_command_safe("echo 'hello; world'") is True


def test_write_creates_nested_directories_inside_workspace(tmp_path):
    result = FileTool().run(
        "write",
        path="nested/deep/result.txt",
        content="hello",
        workspace=str(tmp_path),
    )

    assert result["success"] is True, result
    assert (tmp_path / "nested/deep/result.txt").read_text() == "hello"


def test_write_rejects_parent_symlink_outside_workspace(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "linked"

    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        return

    result = FileTool().run(
        "write",
        path="linked/evil.txt",
        content="should not write",
        workspace=str(tmp_path),
    )

    assert result["success"] is False
    assert not (outside / "evil.txt").exists()


def test_write_rejects_traversal_through_missing_directories(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "outside" / "evil.txt"

    result = FileTool().run(
        "write",
        path="missing/../../outside/evil.txt",
        content="should not be written",
        workspace=str(workspace),
    )

    assert result["success"] is False, result
    assert not outside_file.exists()
