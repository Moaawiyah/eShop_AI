#!/usr/bin/env python3
"""PreToolUse hook for Bash: block prohibited operations that rules cannot express.

Covers forms that prefix-based permission rules miss (for example
`git -C . push -f`, `sh -c '...'`, `bash <<EOF`, `timeout -s KILL 5 aws`,
`/usr/local/bin/aws`, `terraform -chdir=x apply`, commands naming secret files,
`$(...)` substitutions and deletions outside the project). Shells reading
commands from stdin and very deep nesting require approval. Unparseable input
produces no decision; the normal permission flow still applies.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bash_checks import CHECKS, Verdict  # noqa: E402
from hook_lib import decide, project_dir, read_event  # noqa: E402
from shell_parse import (SHELLS, candidate_argvs, command_substitutions,  # noqa: E402
                         shell_heredoc_bodies, shell_scripts, split_commands)

MAX_DEPTH = 3
STDIN_SHELL = ("ask", "A shell reading commands from stdin cannot be checked; approval required.")
TOO_DEEP = ("ask", "Deeply nested shell commands cannot be checked; approval required.")


def evaluate(command: str, cwd: str, project: str, depth: int = 0) -> Verdict | None:
    """Return the strongest verdict ('deny' beats 'ask') across all subcommands."""
    if depth > MAX_DEPTH:
        return TOO_DEEP
    commands = split_commands(command)
    if commands is None:
        return None
    verdicts: list[Verdict] = []
    nested = shell_heredoc_bodies(command) + command_substitutions(command)
    for raw in commands:
        for argv in candidate_argvs(raw):
            program = os.path.basename(argv[0])
            if program == "cd" and len(argv) > 1:
                cwd = os.path.normpath(os.path.join(cwd, os.path.expanduser(argv[1])))
                continue
            if program == "eval":
                nested.append(" ".join(argv[1:]))
                continue
            if program in SHELLS:
                scripts, reads_stdin = shell_scripts(argv)
                nested.extend(scripts)
                if reads_stdin:
                    verdicts.append(STDIN_SHELL)
                continue
            for check in CHECKS:
                verdict = check(program, argv[1:], cwd, project)
                if verdict:
                    verdicts.append(verdict)
    for text in nested:
        verdict = evaluate(text, cwd, project, depth + 1)
        if verdict:
            verdicts.append(verdict)
    if not verdicts:
        return None
    return next((v for v in verdicts if v[0] == "deny"), verdicts[0])


def main() -> int:
    event = read_event()
    command = (event.get("tool_input") or {}).get("command")
    if event.get("tool_name") != "Bash" or not isinstance(command, str):
        return 0
    cwd = str(event.get("cwd") or os.getcwd())
    verdict = evaluate(command, cwd, project_dir(event))
    if verdict:
        decide("PreToolUse", verdict[0], verdict[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
