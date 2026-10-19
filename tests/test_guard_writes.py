import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = PROJECT_DIR / ".claude" / "hooks" / "guard_writes.py"


def run_hook(tool_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    payload = {"tool_name": tool_name, "tool_input": tool_input}
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(PROJECT_DIR)},
        check=False,
    )


@pytest.mark.parametrize("blocked_path", ["utils/errors.py", "DRILL_PROMPTS.md"])
def test_blocked_path_write(blocked_path):
    result = run_hook(
        "Write",
        {"file_path": str(PROJECT_DIR / blocked_path), "content": "anything"},
    )
    assert result.returncode == 2
    assert result.stderr.strip()


@pytest.mark.parametrize(
    "blocked_path",
    ["Utils/errors.py", "UTILS/ERRORS.PY", "utils/../utils/errors.py", "drill_prompts.md"],
)
def test_blocked_path_write_case_and_dotdot_variants(blocked_path):
    result = run_hook(
        "Write",
        {"file_path": str(PROJECT_DIR / blocked_path), "content": "anything"},
    )
    assert result.returncode == 2
    assert result.stderr.strip()


def test_allowed_path_write():
    result = run_hook(
        "Write",
        {"file_path": str(PROJECT_DIR / "services" / "users.py"), "content": "anything"},
    )
    assert result.returncode == 0


def test_connection_string_blocked_edit():
    result = run_hook(
        "Edit",
        {
            "file_path": str(PROJECT_DIR / "services" / "tasks.py"),
            "old_string": "x",
            "new_string": 'DB_URL = "postgresql://user:pass@host/db"',
        },
    )
    assert result.returncode == 2
    assert "connection string" in result.stderr.lower()


def test_connection_string_blocked_multiedit():
    result = run_hook(
        "MultiEdit",
        {
            "file_path": str(PROJECT_DIR / "services" / "tasks.py"),
            "edits": [
                {"old_string": "a", "new_string": "fine = 1"},
                {"old_string": "b", "new_string": 'DB_URL = "sqlite:///tasks.db"'},
            ],
        },
    )
    assert result.returncode == 2


def test_clean_content_allowed_on_tasks_py():
    result = run_hook(
        "Edit",
        {
            "file_path": str(PROJECT_DIR / "services" / "tasks.py"),
            "old_string": "x",
            "new_string": "TASKS: dict[int, dict] = {}",
        },
    )
    assert result.returncode == 0


@pytest.mark.parametrize(
    "command",
    [
        "DROP TABLE users;",
        "truncate table tasks",
        "rm -rf /tmp/scratch",
        "rm -fr /tmp/scratch",
        "rm -r -f /tmp/scratch",
        "git push --force",
        "git push -f origin main",
    ],
)
def test_bash_pattern_blocked(command):
    result = run_hook("Bash", {"command": command})
    assert result.returncode == 2
    assert result.stderr.strip()


@pytest.mark.parametrize(
    "command",
    [
        "git log --oneline",
        "pip install dropbox",
        "rm file.txt",
    ],
)
def test_bash_near_miss_allowed(command):
    result = run_hook("Bash", {"command": command})
    assert result.returncode == 0


@pytest.mark.parametrize(
    "command",
    [
        "echo x >> utils/errors.py",
        "echo x > Utils/errors.py",
        "cat x | tee utils/errors.py",
        "cp /tmp/x utils/errors.py",
        "sed -i s/a/b/ utils/errors.py",
        "git checkout -- utils/errors.py",
    ],
)
def test_bash_indirect_write_to_protected_path_blocked(command):
    result = run_hook("Bash", {"command": command})
    assert result.returncode == 2
    assert result.stderr.strip()


@pytest.mark.parametrize(
    "command",
    [
        "cat utils/errors.py",
        "grep AppError utils/errors.py",
    ],
)
def test_bash_read_of_protected_path_allowed(command):
    result = run_hook("Bash", {"command": command})
    assert result.returncode == 0
