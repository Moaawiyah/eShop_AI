"""Individual command checks used by guard_bash.py.

Each check receives (program, args, cwd, project) for one simple command and
returns (decision, reason) or None. Decisions are 'deny' or 'ask'. The Git
check lives in git_checks.py.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Callable

from git_checks import POLICY, SECRET_READ, Verdict, check_git
from hook_lib import positionals, refers_to_secret

CLOUD_CLIS = {"aws", "gcloud", "gsutil", "az", "eksctl", "pulumi", "doctl"}
DELETERS = {"rm", "rmdir", "unlink", "shred"}
# Programs that may name a secret file without reading its content. Every other
# program naming one is denied: listing all readers (interpreters, json.tool,
# pagers, editors, archivers) is impossible, so the default is deny. Git has its
# own content checks in git_checks.py.
NAME_ONLY = {"ls", "test", "[", "stat", "file", "touch", "chmod", "mkdir", "echo", "printf",
             "git", "find", "which", "type", "basename", "dirname", *DELETERS}
FIND_EXEC = {"-exec", "-execdir", "-ok", "-okdir"}
PATTERN_FIRST = {"grep", "egrep", "fgrep", "rg", "ag", "awk", "sed"}
COPIERS = {"cp", "mv", "scp", "rsync"}
TEMP_ROOTS = tuple({os.path.realpath(p) for p in
                    (tempfile.gettempdir(), "/tmp", "/private/tmp", "/var/folders")})


def check_terraform(program: str, args: list[str], cwd: str, project: str) -> Verdict | None:
    if program not in ("terraform", "tofu"):
        return None
    words = positionals(args)
    sub = words[0] if words else ""
    nxt = words[1] if len(words) > 1 else ""
    if sub in ("apply", "destroy", "import", "taint", "untaint", "force-unlock") or (
            sub == "state" and nxt in ("rm", "mv", "push", "replace-provider")):
        return "deny", f"terraform {sub} is blocked during M0 by {POLICY}."
    if sub in ("plan", "init", "refresh"):
        return "ask", f"terraform {sub} may contact a real cloud account; approval required."
    return None


def check_cloud(program: str, args: list[str], cwd: str, project: str) -> Verdict | None:
    if program in CLOUD_CLIS or (program == "cdk" and args[:1] in (["deploy"], ["destroy"])):
        return "deny", f"Cloud CLI access ({program}) is blocked in M0; AWS access requires {POLICY}."
    return None


def check_secret_reads(program: str, args: list[str], cwd: str, project: str) -> Verdict | None:
    """Deny any command naming a secret file unless it only handles the name."""
    if program in ("curl", "wget"):
        candidates = [m for a in args for m in re.findall(r"@([^\s;&|]+)", a)]
        candidates += [args[i + 1] for i, a in enumerate(args[:-1])
                       if a in ("-T", "--upload-file", "--post-file", "--body-file")]
    elif program in NAME_ONLY and not (program == "find" and FIND_EXEC & set(args)):
        return None
    elif program in COPIERS:
        candidates = positionals(args)[:-1]  # copying an example to .env is allowed
    else:
        candidates = positionals(args)
        if program in PATTERN_FIRST and not {"-e", "-f", "--regexp", "--file"} & set(args):
            candidates = candidates[1:]  # the search pattern may mention .env
    if any(refers_to_secret(c, cwd) for c in candidates):
        return "deny", SECRET_READ
    return None


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def check_deletions(program: str, args: list[str], cwd: str, project: str) -> Verdict | None:
    if program in DELETERS:
        targets = [a for a in args if not a.startswith("-")]
    elif program == "find" and ("-delete" in args or "rm" in args):
        targets = []
        for a in args:
            if a.startswith(("-", "(", "!")):
                break
            targets.append(a)
    else:
        return None
    root = os.path.realpath(project)
    for target in targets:
        if "$" in target or "`" in target:
            return "ask", "Deletion target uses a variable that cannot be verified."
        resolved = os.path.realpath(os.path.join(cwd, os.path.expanduser(target)))
        if program == "find" and resolved == root:
            continue  # find deletes matching entries, not the search root itself
        if _inside(root, resolved):
            return "deny", "Deleting the project directory or one of its parents is blocked."
        if _inside(resolved, root):
            parts = os.path.relpath(resolved, root).lower().split(os.sep)
            if ".git" in parts:  # case-insensitive: macOS treats .GIT as .git
                return "deny", "Deleting Git metadata is blocked."
            continue
        if not any(_inside(resolved, tmp) for tmp in TEMP_ROOTS):
            return "deny", f"Deleting files outside the project ({target}) is blocked."
    return None


CHECKS: tuple[Callable[[str, list[str], str, str], Verdict | None], ...] = (
    check_git, check_terraform, check_cloud, check_secret_reads, check_deletions)
