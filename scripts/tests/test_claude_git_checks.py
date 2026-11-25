"""Regression tests for .claude/hooks/git_checks.py (security review, 2026-11-25).

Simulated inputs only: git is never run and no secret file is read.

Run: python3 -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import unittest

from test_claude_hooks import decision


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


if __name__ == "__main__":
    unittest.main()
