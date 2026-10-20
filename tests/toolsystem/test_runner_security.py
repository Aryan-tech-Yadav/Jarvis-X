import sys
from pathlib import Path

from app.agent.code_runner import CodeRunner
from app.tools.command_runner import CommandRunner


def test_code_runner_executes_valid_script(tmp_path):
    script = tmp_path / "hello.py"
    script.write_text("print('JARVIS_OK')\n", encoding="utf-8")

    success, output = CodeRunner(workspace=tmp_path).run(str(script))

    assert success is True
    assert "JARVIS_OK" in output


def test_code_runner_rejects_missing_script():
    success, output = CodeRunner().run("/tmp/jarvis_missing_script_12345.py")

    assert success is False
    assert output


def test_code_runner_times_out(tmp_path):
    script = tmp_path / "slow.py"
    script.write_text(
        "import time\ntime.sleep(5)\n",
        encoding="utf-8",
    )

    success, output = CodeRunner(timeout=1, workspace=tmp_path).run(str(script))

    assert success is False
    assert "timed out" in output.lower()


def test_command_runner_rejects_invalid_project_path():
    result = CommandRunner().run([sys.executable, "-c", "print('x')"], "")

    assert result.success is False
    assert result.error == "Invalid project path"


def test_command_runner_rejects_invalid_command(tmp_path):
    runner = CommandRunner()

    for command in ([], None, "echo hello", [sys.executable, None]):
        result = runner.run(command, str(tmp_path))
        assert result.success is False


def test_command_runner_executes_valid_command(tmp_path):
    result = CommandRunner().run(
        [sys.executable, "-c", "print('JARVIS_OK')"],
        str(tmp_path),
    )

    assert result.success is True
    assert "JARVIS_OK" in result.output
    assert result.metadata["returncode"] == 0


def test_command_runner_times_out(tmp_path):
    result = CommandRunner(timeout=1).run(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        str(tmp_path),
    )

    assert result.success is False
    assert "timed out" in result.error.lower()

def test_code_runner_rejects_script_outside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("print('OUTSIDE_EXECUTED')\\n", encoding="utf-8")

    success, output = CodeRunner(workspace=workspace).run(str(outside))

    assert success is False
    assert "outside" in output.lower()


def test_code_runner_rejects_symlink_escape(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("print('OUTSIDE_EXECUTED')\\n", encoding="utf-8")
    link = workspace / "linked.py"

    try:
        link.symlink_to(outside)
    except OSError:
        return

    success, output = CodeRunner(workspace=workspace).run(str(link))

    assert success is False
    assert "outside" in output.lower()


def test_code_runner_rejects_non_python_file(tmp_path):
    target = tmp_path / "script.txt"
    target.write_text("not a Python script", encoding="utf-8")

    success, output = CodeRunner(workspace=tmp_path).run(str(target))

    assert success is False
    assert "python" in output.lower()
