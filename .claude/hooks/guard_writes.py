#!/usr/bin/env python3
"""PreToolUse hook guarding protected files, hardcoded DB URLs, and risky Bash commands."""

import json
import os
import re
import sys

BLOCKED_PATHS = ["utils/errors.py", "DRILL_PROMPTS.md"]

CONNECTION_STRING_PATTERN = re.compile(r"postgresql://|sqlite:///", re.IGNORECASE)

BASH_PATTERNS = [
    (
        re.compile(r"\b(?:DROP|TRUNCATE)\s+TABLE\b", re.IGNORECASE),
        "Destructive SQL statement (DROP/TRUNCATE TABLE) is not allowed.",
    ),
    (
        re.compile(r"\brm\b[^|;&]*(?:-(?:rf|fr)\b|-r\s+-f\b|-f\s+-r\b)", re.IGNORECASE),
        "rm with both -r and -f flags is not allowed.",
    ),
    (
        re.compile(r"\bgit\s+push\b[^|;&]*\s(?:--force\b|-f\b)", re.IGNORECASE),
        "git push with --force/-f is not allowed.",
    ),
]


def relative_path(file_path: str, project_dir: str) -> str:
    """Convert a file path to a path relative to the project directory.

    Args:
        file_path: The path given to the tool, absolute or relative.
        project_dir: The project's root directory (CLAUDE_PROJECT_DIR).

    Returns:
        The path relative to project_dir, exactly as computed by os.path.relpath,
        with no case normalization or further cleanup.
    """
    if os.path.isabs(file_path):
        return os.path.relpath(file_path, project_dir)
    return file_path


def new_content_for(tool_name: str, tool_input: dict) -> str:
    """Extract the text a Write/Edit/MultiEdit call would write to disk.

    Args:
        tool_name: One of "Write", "Edit", "MultiEdit".
        tool_input: The tool's input payload.

    Returns:
        The new content (Write), new_string (Edit), or the concatenation of every
        edits[].new_string (MultiEdit).
    """
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return tool_input.get("new_string", "")
    edits = tool_input.get("edits", []) or []
    return "\n".join(edit.get("new_string", "") for edit in edits)


def check_write_like(tool_name: str, tool_input: dict, project_dir: str) -> str | None:
    """Apply the path guard and, for services/tasks.py, the content guard.

    Args:
        tool_name: One of "Write", "Edit", "MultiEdit".
        tool_input: The tool's input payload.
        project_dir: The project's root directory (CLAUDE_PROJECT_DIR).

    Returns:
        A block reason string if the call should be blocked, otherwise None.
    """
    file_path = tool_input.get("file_path", "")
    rel_path = relative_path(file_path, project_dir)

    if rel_path in BLOCKED_PATHS:
        return f"Blocked: {rel_path} is a protected file and cannot be modified."

    if rel_path == "services/tasks.py":
        content = new_content_for(tool_name, tool_input)
        if CONNECTION_STRING_PATTERN.search(content):
            return (
                "Hardcoded database connection string in services/tasks.py — "
                "connection strings must come from environment variables."
            )

    return None


def check_bash(tool_input: dict) -> str | None:
    """Apply the Bash command guard.

    Args:
        tool_input: The tool's input payload.

    Returns:
        A block reason string if the command matches a blocked pattern, otherwise None.
    """
    command = tool_input.get("command", "")
    for pattern, reason in BASH_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def main() -> None:
    """Read a PreToolUse hook payload from stdin and block disallowed calls."""
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    reason = None
    if tool_name in ("Write", "Edit", "MultiEdit"):
        reason = check_write_like(tool_name, tool_input, project_dir)
    elif tool_name == "Bash":
        reason = check_bash(tool_input)

    if reason:
        print(reason, file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
