#!/usr/bin/env python3
"""PostToolUse hook: run the documentation validator after documentation edits.

Runs only when the edited file is one the validator checks. Silent on success;
on failure it adds the validator's error lines to Claude's context. It never
blocks, edits files, commits or calls a network service.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hook_lib import project_dir, read_event  # noqa: E402

WATCHED_PREFIXES = ("docs/", ".claude/rules/", ".vscode/", "scripts/docs_validator/")
WATCHED_FILES = {"README.md", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", ".env.example",
                 "scripts/validate_docs.py"}
MAX_LINES = 15


def is_watched(file_path: str, project: str) -> bool:
    try:
        relative = Path(os.path.realpath(file_path)).relative_to(os.path.realpath(project))
    except ValueError:
        return False
    rel = relative.as_posix()
    return rel in WATCHED_FILES or rel.startswith(WATCHED_PREFIXES)


def main() -> int:
    event = read_event()
    file_path = (event.get("tool_input") or {}).get("file_path")
    project = project_dir(event)
    validator = Path(project) / "scripts/validate_docs.py"
    if not isinstance(file_path, str) or not validator.is_file():
        return 0
    if not is_watched(file_path, project):
        return 0
    try:
        result = subprocess.run([sys.executable, str(validator), "--quiet", "--root", project],
                                capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    if result.returncode == 0:
        return 0
    problems = [line for line in result.stdout.splitlines() if line.startswith("ERROR")]
    summary = "\n".join(problems[:MAX_LINES]) or result.stdout[-1000:]
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "Documentation validation failed after this edit "
                             f"(python3 scripts/validate_docs.py):\n{summary}",
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
