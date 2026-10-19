#!/usr/bin/env python3
"""PreToolUse hook guarding protected files, hardcoded DB URLs, and risky Bash commands."""

import json
import os
import re
import shlex
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

SEPARATOR_TOKENS = {"|", ";", "&&", "||", "&"}
REDIRECT_TOKENS = {">", ">>", "2>", "2>>"}
REDIRECT_OR_SEPARATOR_PATTERN = re.compile(r"(2>>|2>|>>|>|\|\||\||&&|&|;)")


def relative_path(file_path: str, project_dir: str) -> str:
    """Convert a file path to a normalized path relative to the project directory.

    Args:
        file_path: The path given to the tool, absolute or relative.
        project_dir: The project's root directory (CLAUDE_PROJECT_DIR).

    Returns:
        The path relative to project_dir, with ".." segments collapsed via
        os.path.normpath. Case is left as-is; callers compare case-insensitively.
    """
    if not os.path.isabs(file_path):
        file_path = os.path.join(project_dir, file_path)
    normalized = os.path.normpath(file_path)
    return os.path.relpath(normalized, project_dir)


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
    rel_path_lower = rel_path.lower()

    if rel_path_lower in (blocked.lower() for blocked in BLOCKED_PATHS):
        return f"Blocked: {rel_path} is a protected file and cannot be modified."

    if rel_path_lower == "services/tasks.py":
        content = new_content_for(tool_name, tool_input)
        if CONNECTION_STRING_PATTERN.search(content):
            return (
                "Hardcoded database connection string in services/tasks.py — "
                "connection strings must come from environment variables."
            )

    return None


def tokenize_command(command: str) -> list[str]:
    """Split a shell command into tokens, isolating redirection/separator operators.

    Args:
        command: The raw Bash command string.

    Returns:
        The command's tokens, with quoting resolved by shlex where possible and
        each of >, >>, 2>, 2>>, |, ||, &, &&, ; always its own token.
    """
    spaced = REDIRECT_OR_SEPARATOR_PATTERN.sub(r" \1 ", command)
    try:
        return shlex.split(spaced)
    except ValueError:
        return spaced.split()


def split_segments(tokens: list[str]) -> list[list[str]]:
    """Split a token stream into per-command segments at separator tokens.

    Args:
        tokens: Tokens produced by tokenize_command.

    Returns:
        One token list per simple command, with the separators removed.
    """
    segments = []
    current: list[str] = []
    for token in tokens:
        if token in SEPARATOR_TOKENS:
            if current:
                segments.append(current)
            current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def targets_in_segment(segment: list[str]) -> list[str]:
    """Find the paths a single command segment would write to.

    Args:
        segment: The tokens of one simple command (no separators).

    Returns:
        Paths the segment writes to: redirection targets, and, for
        cp/mv/install/tee/sed -i/truncate/rm/git checkout|restore --, their
        write-target arguments.
    """
    targets = []
    for i, token in enumerate(segment):
        if token in REDIRECT_TOKENS and i + 1 < len(segment):
            targets.append(segment[i + 1])

    if not segment:
        return targets

    command, args = segment[0], segment[1:]
    non_flags = [arg for arg in args if not arg.startswith("-")]

    if command in ("cp", "mv", "install") and non_flags:
        targets.append(non_flags[-1])
    elif command in ("tee", "truncate", "rm"):
        targets.extend(non_flags)
    elif command == "sed" and len(non_flags) > 1:
        targets.extend(non_flags[1:])
    elif command == "git" and args[:1] and args[0] in ("checkout", "restore") and "--" in segment:
        targets.extend(segment[segment.index("--") + 1 :])

    return targets


def check_bash(tool_input: dict, project_dir: str) -> str | None:
    """Apply the Bash command guard: blocked patterns, and writes to protected paths.

    Args:
        tool_input: The tool's input payload.
        project_dir: The project's root directory (CLAUDE_PROJECT_DIR).

    Returns:
        A block reason string if the command matches a blocked pattern or targets a
        protected path, otherwise None.
    """
    command = tool_input.get("command", "")
    for pattern, reason in BASH_PATTERNS:
        if pattern.search(command):
            return reason

    blocked_lower = {blocked.lower() for blocked in BLOCKED_PATHS}
    for segment in split_segments(tokenize_command(command)):
        for target in targets_in_segment(segment):
            if relative_path(target, project_dir).lower() in blocked_lower:
                return f"Blocked: {target} is a protected file and cannot be modified."
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
        reason = check_bash(tool_input, project_dir)

    if reason:
        print(reason, file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
