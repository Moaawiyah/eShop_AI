"""Git command check used by guard_bash.py (see bash_checks.CHECKS).

Returns (decision, reason) or None for one simple `git` command.
"""

from __future__ import annotations

import os
import re

from hook_lib import positionals, refers_to_secret

Verdict = tuple[str, str]
POLICY = "project policy (CLAUDE.md section 12)"
SECRET_READ = "Reading or copying secret files is blocked; document settings in .env.example."
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
# Subcommands that print file content; `log` does so only with patch output.
CONTENT_SUBCOMMANDS = {"diff", "grep", "show", "cat-file", "blame", "annotate", "difftool"}
PATCH_OPTIONS = {"--patch", "--patch-with-stat", "--patch-with-raw", "--cc"}


def _short_flags(args: list[str]) -> str:
    return "".join(a[1:] for a in args if re.fullmatch(r"-[A-Za-z]+", a))


def _object_path(arg: str) -> str:
    """Path part of `<rev>:<path>` and `:<stage>:<path>` object names."""
    return arg.rsplit(":", 1)[1] if ":" in arg else arg


def _content_paths(sub: str, rest: list[str]) -> list[str]:
    """Arguments that may name files whose content git prints.

    For `git grep` the search pattern (first positional, or the value of -e in
    any form) is excluded so that searching for the text ".env" stays possible;
    a pattern file named by -f/--file is a content path.
    """
    if sub != "grep":
        return positionals(rest)
    found: list[str] = []
    explicit = skip_next = False
    for arg in rest:
        if skip_next:
            skip_next = False
        elif arg in ("-e", "--regexp"):
            explicit = skip_next = True
        elif arg.startswith("--regexp=") or re.fullmatch(r"-[A-Za-z]*e.+", arg):
            explicit = True
        elif arg in ("-f", "--file"):
            explicit = True  # the next token is a pattern file and stays a content path
        elif arg.startswith("--file=") or re.fullmatch(r"-[A-Za-z]*f.+", arg):
            explicit = True
            found.append(arg.split("=", 1)[1] if arg.startswith("--") else arg[arg.index("f") + 1:])
        elif not arg.startswith("-"):
            found.append(arg)
    return found if explicit else found[1:]


def _outside(arg: str, cwd: str, project: str) -> bool:
    root = os.path.realpath(project)
    resolved = os.path.realpath(os.path.join(cwd, os.path.expanduser(_object_path(arg))))
    return not (resolved == root or resolved.startswith(root.rstrip(os.sep) + os.sep))


def check_git(program: str, args: list[str], cwd: str, project: str) -> Verdict | None:
    if program != "git":
        return None
    rest = list(args)
    while rest and rest[0].startswith("-"):
        option = rest.pop(0)
        if option in GIT_VALUE_OPTIONS and rest:
            rest.pop(0)
    if not rest:
        return None
    sub, rest = rest[0], rest[1:]
    flags = _short_flags(rest)
    if sub == "push" and ("f" in flags or any(a == "--mirror" or a.startswith(("--force", "+"))
                                              for a in rest)):
        return "deny", f"Force pushes are blocked by {POLICY}."
    if sub in ("push", "commit") and ("--no-verify" in rest or (sub == "commit" and "n" in flags)):
        return "ask", "Skipping Git hooks (--no-verify) requires explicit owner approval."
    if (sub == "branch" and ("d" in flags.lower() or "--delete" in rest)) or (
            sub == "push" and ("d" in flags or "--delete" in rest
                               or any(a.startswith(":") for a in rest))):
        return "ask", "Deleting branches requires explicit owner approval."
    if (sub == "clean" or (sub == "reset" and "--hard" in rest)
            or (sub == "stash" and rest[:1] in (["drop"], ["clear"]))
            or (sub in ("checkout", "restore") and {"--", "."} & set(rest)
                and "--staged" not in rest)):
        return "ask", "This Git command can discard uncommitted work; owner approval required."
    if sub == "add" and any(refers_to_secret(a, cwd) for a in positionals(rest)):
        return "deny", "Staging a secret file is blocked; secrets stay in git-ignored files."
    if sub == "add" and ("--force" in rest or "f" in flags):
        return "ask", "Force-adding git-ignored files requires approval (they may be secrets)."
    paths = _content_paths(sub, rest)
    prints_content = sub in CONTENT_SUBCOMMANDS or (
        sub == "log" and ("p" in flags or "u" in flags or bool(PATCH_OPTIONS & set(rest))))
    if prints_content and any(refers_to_secret(_object_path(a), cwd) for a in paths):
        return "deny", SECRET_READ
    # `git diff a b` silently becomes --no-index when a path is outside the repository.
    untracked = sub == "grep" and bool({"--untracked", "--no-exclude-standard"} & set(rest))
    if sub in ("diff", "grep") and ("--no-index" in rest or untracked
                                     or any(_outside(a, cwd, project) for a in paths)):
        return "ask", f"git {sub} on files outside the repository requires approval."
    if sub in ("diff", "log", "show") and any(a.startswith("--output") for a in rest):
        return "ask", "git --output writes files; confirm the destination."
    return None
