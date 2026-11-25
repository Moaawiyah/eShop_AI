"""Shared helpers for eShop_AI Claude Code hooks.

Standard library only, deterministic, no network access and no LLM calls.
Hooks are defense in depth on top of the permission rules in
.claude/settings.json; they are not a security sandbox.
"""

from __future__ import annotations

import json
import os
import re
import sys
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from typing import Any, NoReturn

SAFE_SUFFIXES = (".example", ".sample", ".template", ".pub")
SECRET_NAMES = {"credentials.json", ".netrc", ".pgpass", ".git-credentials", ".npmrc",
                ".pypirc", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".tfstate",
                   ".tfvars", ".tfvars.json")
SECRET_DIRS = {".aws", ".ssh", ".gnupg"}
SECRET_PATH_PARTS = (".kube/config", ".docker/config.json", ".config/gh/hosts.yml")
SECRET_SAMPLES = (".env", ".env.local", ".env.production", "server.pem", "server.key",
                  "credentials.json", "id_rsa", "terraform.tfstate", "prod.tfvars")
SECRET_MARKERS = ("env", "pem", "key", "cred", "id_", "tfstate", "tfvars")

# High-confidence credential formats only, to avoid blocking normal writing.
SECRET_CONTENT = (
    ("AWS access key ID", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("private key", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{32,}")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{20,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Atlassian API token", re.compile(r"\bATATT3[A-Za-z0-9_=-]{40,}")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}")),
)


def read_event() -> dict[str, Any]:
    """Parse the hook event from stdin; return {} when it is not valid JSON."""
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def decide(event_name: str, decision: str, reason: str) -> NoReturn:
    """Emit a PreToolUse permission decision ('deny' or 'ask') and exit."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": event_name,
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def project_dir(event: dict[str, Any]) -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or str(event.get("cwd") or os.getcwd())


def is_secret_path(raw: str) -> bool:
    """True for paths that commonly hold real credentials (examples excluded).

    Matching is case-insensitive: the default macOS file system treats `.ENV`
    and `.env` as the same file.
    """
    path = raw.strip().strip("'\"").replace("\\", "/").lower()
    if not path:
        return False
    pure = PurePosixPath(path)
    name = pure.name
    if not name or name.endswith(SAFE_SUFFIXES):
        return False
    if name == ".env" or name.startswith(".env."):
        return True
    if name in SECRET_NAMES or name.endswith(SECRET_SUFFIXES) or ".tfstate." in name:
        return True
    if SECRET_DIRS & set(pure.parts) and name != "known_hosts":
        return True
    return any(part in path for part in SECRET_PATH_PARTS)


def matches_secret_glob(raw: str) -> bool:
    """True when a glob such as '.env*' explicitly targets secret files.

    Generic globs ('*', '*.*', '**/*.md') are not flagged, to avoid blocking searches.
    """
    pattern = PurePosixPath(raw.strip().strip("'\"")).name.lower()
    if not any(c in pattern for c in "*?[") or not any(m in pattern for m in SECRET_MARKERS):
        return False
    return any(fnmatchcase(sample, pattern) for sample in SECRET_SAMPLES)


def secret_reference(raw: str) -> bool:
    return is_secret_path(raw) or matches_secret_glob(raw)


def refers_to_secret(raw: str, cwd: str) -> bool:
    """True when ``raw`` names a secret path directly or through a symlink.

    Resolving a path only inspects links; no file content is read.
    """
    if secret_reference(raw):
        return True
    try:
        resolved = os.path.realpath(os.path.join(cwd, os.path.expanduser(raw.strip("'\""))))
    except (OSError, ValueError):
        return False
    return is_secret_path(resolved)


def find_secret_content(text: str) -> str | None:
    """Return the kind of credential found in ``text`` (never the value), or None."""
    for kind, pattern in SECRET_CONTENT:
        if pattern.search(text):
            return kind
    return None
