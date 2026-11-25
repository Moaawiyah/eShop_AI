"""Individual command checks used by guard_bash.py.

Each check receives (program, args, cwd, project) for one simple command and
returns (decision, reason) or None. Decisions are 'deny' or 'ask'.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Callable

from hook_lib import refers_to_secret

Verdict = tuple[str, str]
POLICY = "project policy (CLAUDE.md section 12)"
SECRET_READ = "Reading or copying secret files is blocked; document settings in .env.example."
CLOUD_CLIS = {"aws", "gcloud", "gsutil", "az", "eksctl", "pulumi", "doctl"}
DELETERS = {"rm", "rmdir", "unlink", "shred"}
# Programs that may name a secret file without reading its content. Every other
# program naming one is denied: listing all readers (interpreters, json.tool,
# pagers, editors, archivers) is impossible, so the default is deny.
NAME_ONLY = {"ls", "test", "[", "stat", "file", "touch", "chmod", "mkdir", "echo", "printf",
             "git", "find", "which", "type", "basename", "dirname", *DELETERS}
FIND_EXEC = {"-exec", "-execdir", "-ok", "-okdir"}
PATTERN_FIRST = {"grep", "egrep", "fgrep", "rg", "ag", "awk", "sed"}
COPIERS = {"cp", "mv", "scp", "rsync"}
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
TEMP_ROOTS = tuple({os.path.realpath(p) for p in
                    (tempfile.gettempdir(), "/tmp", "/private/tmp", "/var/folders")})


def _short_flags(args: list[str]) -> str:
    return "".join(a[1:] for a in args if re.fullmatch(r"-[A-Za-z]+", a))


def _positionals(args: list[str]) -> list[str]:
    return [a for a in args if not a.startswith("-")]


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
    flags, positionals = _short_flags(rest), _positionals(rest)
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
    if sub == "add" and any(refers_to_secret(a, cwd) for a in positionals):
        return "deny", "Staging a secret file is blocked; secrets stay in git-ignored files."
    if sub == "add" and ("--force" in rest or "f" in flags):
        return "ask", "Force-adding git-ignored files requires approval (they may be secrets)."
    if sub in ("diff", "grep") and "--no-index" in rest:
        if any(refers_to_secret(a, cwd) for a in positionals):
            return "deny", SECRET_READ
        return "ask", "git --no-index reads files outside version control; confirm the paths."
    if sub in ("show", "cat-file") and any(
            ":" in a and refers_to_secret(a.split(":", 1)[1], cwd) for a in positionals):
        return "deny", SECRET_READ
    if sub in ("diff", "log", "show") and any(a.startswith("--output") for a in rest):
        return "ask", "git --output writes files; confirm the destination."
    return None


def check_terraform(program: str, args: list[str], cwd: str, project: str) -> Verdict | None:
    if program not in ("terraform", "tofu"):
        return None
    positionals = _positionals(args)
    sub = positionals[0] if positionals else ""
    nxt = positionals[1] if len(positionals) > 1 else ""
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
        candidates = _positionals(args)[:-1]  # copying an example to .env is allowed
    else:
        candidates = _positionals(args)
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
