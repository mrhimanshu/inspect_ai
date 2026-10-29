"""Setup failures must remain visible when evaluation progress is hidden."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("options", "stream"),
    [
        (["--display", "none"], "stderr"),
        (["--display", "plain"], "stdout"),
        (["--display", "none", "--no-ansi"], "stdout"),
        (["--display", "none", "--json"], "stderr"),
    ],
)
def test_cli_prerequisite_error_is_visible(
    tmp_path: Path, options: list[str], stream: str
) -> None:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("INSPECT_")
    }
    env.update(FORCE_COLOR="1", TERM="xterm-256color")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "inspect_ai",
            "eval",
            "missing_task.py",
            "--model",
            "mockllm/model",
            *options,
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 1
    assert "No inspect tasks were found" in getattr(result, stream)
    assert getattr(result, "stdout" if stream == "stderr" else "stderr") == ""
    assert "Traceback" not in result.stdout + result.stderr
    assert "\x1b[" not in result.stdout + result.stderr


def test_python_eval_prerequisite_error_is_visible(tmp_path: Path) -> None:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("INSPECT_")
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from inspect_ai import Task, eval; "
            "from inspect_ai.dataset import Sample; "
            "eval(Task(dataset=[Sample(input='hi')]), model='mockllm/model', "
            "cost_limit=1.0, display='none')",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "cost_limit requires cost data" in result.stderr
    assert "Traceback" not in result.stderr
    assert "\x1b[" not in result.stderr
