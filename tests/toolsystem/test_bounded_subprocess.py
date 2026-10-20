import sys

from app.tools.process_utils import run_bounded


def test_normal_stdout_and_stderr_are_captured():
    result = run_bounded(
        [
            sys.executable,
            "-c",
            "import sys; print('x' * 50); print('y' * 50, file=sys.stderr)",
        ],
        max_output_chars=100,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == "x" * 50 + "\n"
    assert result.stderr == "y" * 50 + "\n"


def test_chatty_stdout_is_capped_and_process_terminated():
    result = run_bounded(
        [
            sys.executable,
            "-u",
            "-c",
            "exec(\"while True: print('x' * 1000, flush=True)\")",
        ],
        max_output_chars=256,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode != 0
    assert len(result.stdout) < 300
    assert result.stdout.endswith("...[output truncated]")


def test_chatty_stderr_is_capped_and_process_terminated():
    result = run_bounded(
        [
            sys.executable,
            "-u",
            "-c",
            "import sys; exec(\"while True: print('y' * 1000, file=sys.stderr, flush=True)\")",
        ],
        max_output_chars=256,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode != 0
    assert len(result.stderr) < 300
    assert result.stderr.endswith("...[output truncated]")


def test_output_cap_cleans_up_child_after_parent_exits():
    import os
    import time

    if os.name != "posix":
        return

    code = (
        "import subprocess, sys; "
        "subprocess.Popen([sys.executable, '-c', "
        "'import time; time.sleep(30)']); "
        "print('x' * 1000, flush=True)"
    )

    started = time.monotonic()
    result = run_bounded(
        [sys.executable, "-u", "-c", code],
        max_output_chars=100,
        text=True,
        timeout=3,
        check=False,
    )
    elapsed = time.monotonic() - started

    assert result.stdout.endswith("...[output truncated]")
    assert elapsed < 5, f"Subprocess cleanup took too long: {elapsed:.2f}s"
