"""Approximate shell parsing for guard_bash.py (standard library only).

This is not a shell parser. When unsure it reports more candidate commands,
never fewer, so checks err towards a decision; the permission rules and the
owner's approval remain the primary controls.
"""

from __future__ import annotations

import os
import re
import shlex

SEPARATORS = {"&&", "||", ";", "|", "|&", "&", "(", ")", ";;", "&;"}
WRAPPERS = {"sudo", "command", "builtin", "exec", "nohup", "time", "nice", "env", "xargs",
            "stdbuf", "timeout", "caffeinate"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# Groups: 1 quote, 2 delimiter, 3 rest of the opening line, 4 body.
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n(.*?)\n\s*\2[ \t]*(?=\n|$)", re.S)
SHELL_C_FLAG = re.compile(r"-[A-Za-z]*c[A-Za-z]*")


def split_commands(text: str) -> list[list[str]] | None:
    """Split shell text into simple commands; None when it cannot be tokenized."""
    text = HEREDOC.sub(lambda m: m.group(3), text)  # bodies are data unless fed to a shell
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


def _split_string(token: str, following: str | None) -> list[str] | None:
    """Arguments of `env -S 'cmd args'` (also -S'...' and --split-string=...)."""
    if token in ("-S", "--split-string"):
        value = following
    elif token.startswith("--split-string="):
        value = token.split("=", 1)[1]
    elif token.startswith("-S") and len(token) > 2:
        value = token[2:]
    else:
        return None
    try:
        return shlex.split(value or "")
    except ValueError:
        return None


def candidate_argvs(argv: list[str]) -> list[list[str]]:
    """Commands that ``argv`` may run.

    Wrapper options can take values (`timeout -s KILL 5 aws`, `nice -n 5 aws`),
    so instead of modelling each wrapper's grammar every non-option position
    after a wrapper is tried. This is linear and errs towards more checks.
    """
    args = list(argv)
    while args and ASSIGNMENT.match(args[0]):
        args.pop(0)
    if not args:
        return []
    if os.path.basename(args[0]) not in WRAPPERS:
        return [args]
    found: list[list[str]] = []
    for index in range(1, len(args)):
        token = args[index]
        following = args[index + 1] if index + 1 < len(args) else None
        split = _split_string(token, following) if os.path.basename(args[0]) == "env" else None
        if split:
            found.append(split)
        elif not token.startswith("-") and not ASSIGNMENT.match(token):
            found.append(args[index:])
    return found


def shell_scripts(argv: list[str]) -> tuple[list[str], bool]:
    """Scripts a shell invocation runs, and whether it reads commands from stdin.

    Handles `-c` alone or in groups (`-lc`) and here-strings (`<<<`).
    """
    rest = argv[1:]
    for index, token in enumerate(rest):
        if SHELL_C_FLAG.fullmatch(token) or token == "<<<":
            return [rest[index + 1] if index + 1 < len(rest) else ""], False
    reads_stdin = "-s" in rest or all(token.startswith("-") for token in rest)
    return [], reads_stdin


def shell_heredoc_bodies(text: str) -> list[str]:
    """Bodies of heredocs fed to a shell (`bash <<EOF`): commands, not data."""
    bodies = []
    for match in HEREDOC.finditer(text):
        line = text[text.rfind("\n", 0, match.start()) + 1:match.start()]
        commands = split_commands(line) or [[]]
        if any(os.path.basename(c[0]) in SHELLS for c in candidate_argvs(commands[-1])):
            bodies.append(match.group(4))
    return bodies


def command_substitutions(text: str) -> list[str]:
    """Contents of `$(...)` and backticks outside single quotes and quoted heredocs.

    Bash runs substitutions inside double quotes and unquoted heredocs too.
    """
    text = HEREDOC.sub(lambda m: m.group(3) if m.group(1) else m.group(0), text)
    found: list[str] = []
    index, quote = 0, ""
    while index < len(text):
        char = text[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if quote == "'":
            quote = "" if char == "'" else quote
        elif char == "'" and not quote:
            quote = "'"
        elif char == '"':
            quote = "" if quote else '"'
        elif char == "`":
            end = text.find("`", index + 1)
            found.append(text[index + 1:end if end != -1 else len(text)])
            index = end if end != -1 else len(text)
        elif text.startswith("$(", index):
            depth, end = 1, index + 2
            while end < len(text) and depth:
                depth += {"(": 1, ")": -1}.get(text[end], 0)
                end += 1
            found.append(text[index + 2:end - 1])
            index = end - 1
        index += 1
    return found
