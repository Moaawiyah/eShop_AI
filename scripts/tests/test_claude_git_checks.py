"""Regression tests for .claude/hooks/git_checks.py (security review, 2026-11-25).

Simulated inputs only: git is never run and no secret file is read.

Run: python3 -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from test_claude_hooks import decision

SETTINGS = Path(__file__).resolve().parents[2] / ".claude" / "settings.json"


class GitContentTests(unittest.TestCase):
    DENY = [
        "git diff /dev/null .env",  # implicit --no-index: one path is outside the repository
        "git diff -- /dev/null .env", "git diff ~/.aws/credentials /dev/null",
        "git show :0:.env", "git show HEAD:./.env", "git log -p -- .env",
        "git log --patch -- backend/.env.local", "git blame .env", "git grep KEY -- .env",
        "git grep -f .env", "git grep --regexp=KEY .env", "git grep -eKEY .env",
        "git grep --file=.env", "git grep -f.env",
    ]
    ASK = ["git diff /dev/null README.md", "git diff ../other-repo/notes.md README.md",
           "git diff --no-index a.txt b.txt", "git grep --untracked TODO",
           "git grep --untracked --no-exclude-standard KEY"]
    ALLOW = [
        "git log --all --oneline -- .env", "git grep -n '.env' -- docs", "git grep -e .env -- docs",
        "git grep --regexp=.env -- docs",
        "git diff origin/main...HEAD", "git diff HEAD~1 -- README.md", "git show HEAD:README.md",
        "git log -p -- README.md", "git blame README.md", "git check-ignore -v .env",
    ]

    def check(self, commands: list[str], expected: str | None) -> None:
        for cmd in commands:
            with self.subTest(cmd=cmd):
                self.assertEqual(decision(cmd), expected)

    def test_secret_content_is_denied(self) -> None:
        self.check(self.DENY, "deny")

    def test_files_outside_the_repository_require_approval(self) -> None:
        self.check(self.ASK, "ask")

    def test_ordinary_git_use_is_unaffected(self) -> None:
        self.check(self.ALLOW, None)


class GitFollowUpTests(GitContentTests):
    """Second review (2026-11-25): option values, global options and input-driven reads."""

    DENY = [
        "git log -U3 -- .env", "git log --word-diff -- .env", "git whatchanged -p .env",
        "git format-patch --stdout -- .env", "git grep -if .env", "git log -L1,5:.env",
        "git log -L1,5:backend/.ENV.local", "git show --format=%B HEAD:.env",
    ]
    ASK = [
        "git -C ~/.aws diff credentials config", "git -C .. status",
        "git --git-dir=/tmp/other/.git show HEAD:notes", "git --work-tree=/ diff",
        "git -c core.pager=cat log", "git cat-file --batch", "git cat-file --batch-check",
        "git diff --stdin",
    ]
    ALLOW = [
        "git -C . status", "git -C docs log --oneline", "git log --oneline -- .env",
        "git log --all --format=%H -n 3 -- .env", "git rm --cached .env",
        "git status --short .env", "git ls-files --error-unmatch .env.example",
        "git diff -- .env.example", "git diff --stat main...HEAD", "git grep -ie .env -- docs",
        "git log -p -- docs/PRD.md", "git log -U3 -- README.md", "git grep -n TODO -- scripts",
    ]


class GitAllowRuleTests(unittest.TestCase):
    def test_content_printing_git_commands_have_no_wildcard_allow(self) -> None:
        rules = json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"]["allow"]
        for sub in ("diff", "log", "show", "blame", "grep", "cat-file"):
            with self.subTest(sub=sub):
                self.assertFalse([r for r in rules if r.startswith(f"Bash(git {sub}") and "*" in r])


if __name__ == "__main__":
    unittest.main()
