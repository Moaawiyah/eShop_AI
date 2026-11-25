#!/usr/bin/env python3
"""PreToolUse hook for Bash: block prohibited operations that rules cannot express.

Covers forms that prefix-based permission rules miss (for example
`git -C . push -f`, `sh -c '...'`, `/usr/local/bin/aws`, `terraform -chdir=x apply`,
reads of `.env.*` other than examples, and deletions outside the project).
Unparseable input produces no decision; the normal permission flow still applies.
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bash_checks import CHECKS, Verdict  # noqa: E402
from hook_lib import decide, project_dir, read_event  # noqa: E402

SEPARATORS = {"&&", "||", ";", "|", "|&", "&", "(", ")", ";;", "&;"}
WRAPPERS = {"sudo", "command", "builtin", "exec", "nohup", "time", "nice", "env", "xargs",
            "stdbuf", "timeout", "caffeinate"}
SHELLS = {"sh", "bash", "zsh", "dash"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n.*?\n\s*\2[ \t]*(?=\n|$)", re.S)
MAX_DEPTH = 3


def split_commands(text: str) -> list[list[str]] | None:
    """Split shell text into simple commands; None when it cannot be tokenized."""
    text = HEREDOC.sub(lambda m: m.group(3), text)  # heredoc bodies are data, not commands
    lexer = shlex.shlex(text.replace("\n", " ; "), posix=True, punctuation_chars=";&|()<>")
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    commands: list[list[str]] = [[]]
    for token in tokens:
        if token in SEPARATORS:
            commands.append([])
        else:
            commands[-1].append(token)
    return [c for c in commands if c]


def strip_wrappers(argv: list[str]) -> list[str]:
    """Drop leading VAR=value assignments and wrappers such as sudo or timeout."""
    args = list(argv)
    while args:
        head = os.path.basename(args[0])
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", args[0]):
            args.pop(0)
        elif head in WRAPPERS:
            args.pop(0)
            while args and args[0].startswith("-"):
                args.pop(0)
            if head == "timeout" and args and re.fullmatch(r"[\d.]+[smhd]?", args[0]):
                args.pop(0)
        else:
            break
    return args


def evaluate(command: str, cwd: str, project: str, depth: int = 0) -> Verdict | None:
    """Return the strongest verdict ('deny' beats 'ask') across all subcommands."""
    commands = split_commands(command)
    if commands is None or depth > MAX_DEPTH:
        return None
    verdicts: list[Verdict] = []
    for raw in commands:
        argv = strip_wrappers(raw)
        if not argv:
            continue
        program = os.path.basename(argv[0])
        if program == "cd" and len(argv) > 1:
            cwd = os.path.normpath(os.path.join(cwd, os.path.expanduser(argv[1])))
            continue
        if program in SHELLS and "-c" in argv[1:]:
            index = argv.index("-c")
            if index + 1 < len(argv):
                nested = evaluate(argv[index + 1], cwd, project, depth + 1)
                if nested:
                    verdicts.append(nested)
            continue
        if program == "eval":
            nested = evaluate(" ".join(argv[1:]), cwd, project, depth + 1)
            if nested:
                verdicts.append(nested)
            continue
        for check in CHECKS:
            verdict = check(program, argv[1:], cwd, project)
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
