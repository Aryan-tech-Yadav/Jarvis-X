"""Subprocess execution with bounded in-memory output capture."""

import os
import signal
import subprocess
import threading


def run_bounded(args, *, max_output_chars=20000, **kwargs):
    """Run a subprocess with capped output and timeout cleanup.

    Output is capped independently for stdout and stderr.
    On POSIX, the subprocess starts in a new session so its process
    group can be terminated when the timeout or output cap is exceeded.
    """
    if (
        isinstance(max_output_chars, bool)
        or not isinstance(max_output_chars, int)
        or max_output_chars < 1
    ):
        raise ValueError("max_output_chars must be a positive integer")

    kwargs.pop("capture_output", None)
    text_mode = kwargs.pop("text", True)
    check = kwargs.pop("check", False)
    encoding = kwargs.pop("encoding", None) or "utf-8"
    errors = kwargs.pop("errors", None) or "replace"
    timeout = kwargs.pop("timeout", None)
    input_data = kwargs.pop("input", None)

    if kwargs.get("stdout") is not None or kwargs.get("stderr") is not None:
        raise ValueError("stdout/stderr are managed by run_bounded")
    if "stdin" in kwargs:
        raise ValueError("stdin is managed by run_bounded")

    marker = b"\n...[output truncated]"
    output = {
        "stdout": bytearray(),
        "stderr": bytearray(),
        "stdout_truncated": False,
        "stderr_truncated": False,
    }
    lock = threading.Lock()
    process_holder = {"process": None}

    def build_output():
        with lock:
            stdout = bytes(output["stdout"])
            stderr = bytes(output["stderr"])
            stdout_truncated = output["stdout_truncated"]
            stderr_truncated = output["stderr_truncated"]

        if stdout_truncated:
            stdout += marker
        if stderr_truncated:
            stderr += marker

        if text_mode:
            return (
                stdout.decode(encoding, errors=errors),
                stderr.decode(encoding, errors=errors),
            )
        return stdout, stderr

    def terminate_process():
        process = process_holder["process"]
        if process is None:
            return

        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                try:
                    if process.poll() is None:
                        process.kill()
                except OSError:
                    pass
        elif process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass

    def drain(stream, key):
        truncated_key = f"{key}_truncated"

        while True:
            chunk = stream.read1(4096)
            if not chunk:
                break

            with lock:
                remaining = max_output_chars - len(output[key])
                if remaining > 0:
                    output[key].extend(chunk[:remaining])

                if len(chunk) > max(remaining, 0):
                    output[truncated_key] = True

                should_terminate = output[truncated_key]

            if should_terminate:
                terminate_process()
                # Continue draining/discarding until the pipe closes.

    popen_kwargs = dict(kwargs)
    if os.name == "posix":
        # Allows timeout/output-limit cleanup to kill the process group.
        popen_kwargs["start_new_session"] = True

    if input_data is not None:
        popen_kwargs["stdin"] = subprocess.PIPE

    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **popen_kwargs,
    )
    process_holder["process"] = process

    readers = [
        threading.Thread(
            target=drain, args=(process.stdout, "stdout"), daemon=True
        ),
        threading.Thread(
            target=drain, args=(process.stderr, "stderr"), daemon=True
        ),
    ]

    for reader in readers:
        reader.start()

    writer = None
    if input_data is not None:

        def write_input():
            try:
                payload = input_data
                if isinstance(payload, str):
                    payload = payload.encode(encoding, errors=errors)
                process.stdin.write(payload)
                process.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                pass
            finally:
                try:
                    process.stdin.close()
                except (OSError, ValueError):
                    pass

        writer = threading.Thread(target=write_input, daemon=True)
        writer.start()

    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        terminate_process()
        process.wait()

        for reader in readers:
            reader.join()

        if writer is not None:
            writer.join(timeout=1)

        stdout, stderr = build_output()
        raise subprocess.TimeoutExpired(
            args, timeout, output=stdout, stderr=stderr
        )

    for reader in readers:
        reader.join()

    if writer is not None:
        writer.join(timeout=1)

    stdout, stderr = build_output()
    result = subprocess.CompletedProcess(args, returncode, stdout, stderr)

    if check and returncode != 0:
        raise subprocess.CalledProcessError(
            returncode, args, output=stdout, stderr=stderr
        )

    return result
