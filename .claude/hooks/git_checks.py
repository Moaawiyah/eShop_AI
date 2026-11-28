"""Git command check used by guard_bash.py (see bash_checks.CHECKS).

Returns (decision, reason) or None for one simple `git` command. The secret
rule fails closed: a git command that names a secret path anywhere (argument,
option value or `<rev>:<path>` object) is denied unless the subcommand only
handles file names.
"""

from __future__ import annotations

import os
import re

from hook_lib import positionals, refers_to_secret

Verdict = tuple[str, str]
POLICY = "project policy (CLAUDE.md section 12)"
SECRET_READ = "Reading or copying secret files is blocked; document settings in .env.example."
# Global options that change the repository, configuration or executed programs.
RISKY_GLOBALS = ("-c", "--git-dir", "--work-tree", "--exec-path", "--config-env")
NAME_ONLY = {"status", "check-ignore", "check-attr", "ls-files", "rm"}
SAFE_LOG = re.compile(r"--(oneline|stat|shortstat|name-only|name-status|all|follow|graph|"
                      r"(no-)?decorate|reverse|no-merges|first-parent|abbrev-commit)|-n|-\d+|"
                      r"--(max-count|since|until|author|format|pretty|date)=.*|--")


def _short_flags(args: list[str]) -> str:
    return "".join(a[1:] for a in args if re.fullmatch(r"-[A-Za-z]+", a))


def _object_path(arg: str) -> str:
    """Path part of `<rev>:<path>` and `:<stage>:<path>` object names."""
    return arg.rsplit(":", 1)[1] if ":" in arg else arg


def _grep_paths(rest: list[str]) -> list[str]:
    """`git grep` positionals without the search pattern (first one, unless -e/-f is used)."""
    explicit = skip_next = False
    found: list[str] = []
    for arg in rest:
        if skip_next:
            skip_next = False
        elif arg == "--regexp" or re.fullmatch(r"-[A-Za-z]*e", arg):  # -e, -ie: next is a pattern
            explicit = skip_next = True
        elif arg == "--file" or arg.startswith(("--regexp=", "--file=")) or re.fullmatch(
                r"-[A-Za-z]*[ef].*", arg):  # -f, -if: the next token stays a named path
            explicit = True  # a pattern file stays a named path (see _named_paths)
        elif not arg.startswith("-"):
            found.append(arg)
    return found if explicit else found[1:]


def _named_paths(sub: str, rest: list[str]) -> list[str]:
    """Every argument part that may name a file: positionals and option values."""
    names = _grep_paths(rest) if sub == "grep" else positionals(rest)
    for arg in rest:
        if arg.startswith("--") and "=" in arg and not arg.startswith("--regexp="):
            names.append(arg.split("=", 1)[1])
        elif re.fullmatch(r"-[^-].+", arg) and not (sub == "grep" and re.fullmatch(
                r"-[A-Za-z]*e.+", arg)):
            names += [arg[i:] for i in range(2, len(arg))]  # attached values, e.g. -L1,5:.env
    return [part for name in names for part in (name, _object_path(name))]


def _outside(arg: str, cwd: str, project: str) -> bool:
    root = os.path.realpath(project)
    resolved = os.path.realpath(os.path.join(cwd, os.path.expanduser(_object_path(arg))))
    return not (resolved == root or resolved.startswith(root.rstrip(os.sep) + os.sep))


def _check_secrets(sub: str, rest: list[str], cwd: str, project: str) -> Verdict | None:
    paths = _named_paths(sub, rest)
    safe_log = sub == "log" and all(SAFE_LOG.fullmatch(a) for a in rest if a.startswith("-"))
    if sub not in NAME_ONLY and not safe_log and any(refers_to_secret(p, cwd) for p in paths):
        return "deny", SECRET_READ
    if any(a == "--stdin" or a.startswith(("--batch", "--pathspec-from-file")) for a in rest):
        return "ask", "git reading object names or paths from input requires approval."
    untracked = sub == "grep" and bool({"--untracked", "--no-exclude-standard"} & set(rest))
    # `git diff a b` silently becomes --no-index when a path is outside the repository.
    if sub in ("diff", "grep") and ("--no-index" in rest or untracked or any(
            _outside(a, cwd, project) for a in positionals(rest))):
        return "ask", f"git {sub} on files outside the repository requires approval."
    if sub in ("diff", "log", "show") and any(a.startswith("--output") for a in rest):
        return "ask", "git --output writes files; confirm the destination."
    return None


def check_git(program: str, args: list[str], cwd: str, project: str) -> Verdict | None:
    if program != "git":
        return None
    rest = list(args)
    while rest and rest[0].startswith("-"):
        option = rest.pop(0)
        if option.startswith(RISKY_GLOBALS):
            return "ask", "Git options that change the repository or configuration need approval."
        if option == "-C" and rest:
            cwd = os.path.join(cwd, os.path.expanduser(rest.pop(0)))
            if _outside(cwd, cwd, project):
                return "ask", "git -C outside the project requires approval."
        elif option == "--namespace" and rest:
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
    return _check_secrets(sub, rest, cwd, project)
