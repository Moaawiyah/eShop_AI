"""Tests for the Claude agent and skill checks in scripts/docs_validator/claude_config.py.

Each mutation test copies .claude/ and the referenced documents into a temporary
directory, introduces one defect and asserts that the check reports it.

Run: python3 -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from docs_validator.claude_config import check_agents, check_skills, parse_frontmatter  # noqa: E402
from docs_validator.core import Context, ParseError  # noqa: E402

AGENT = ".claude/agents/security-reviewer.md"
SKILL = ".claude/skills/prepare-commit/SKILL.md"


class FrontmatterTests(unittest.TestCase):
    def test_parses_flat_fields_and_body(self) -> None:
        fields, body = parse_frontmatter('---\nname: x\ndescription: "a: b"\n---\nBody\n', "t")
        self.assertEqual(fields, {"name": "x", "description": "a: b"})
        self.assertEqual(body, "Body\n")

    def test_rejects_missing_unclosed_or_nested_frontmatter(self) -> None:
        for text in ("name: x\n", "---\nname: x\n", "---\ntools:\n  - Read\n---\n",
                     "---\nname: a\nname: b\n---\n"):
            with self.subTest(text=text), self.assertRaises(ParseError):
                parse_frontmatter(text, "t")


class ClaudeConfigMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for directory in (".claude", "docs", "scripts"):
            shutil.copytree(REPO / directory, self.tmp / directory,
                            ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md", "README.md"):
            shutil.copy(REPO / name, self.tmp / name)

    def errors(self) -> list[str]:
        ctx = Context(root=self.tmp)
        check_agents(ctx)
        check_skills(ctx)
        return ctx.report.errors

    def mutate(self, relative: str, change: Callable[[str], str]) -> list[str]:
        path = self.tmp / relative
        original = path.read_text(encoding="utf-8")
        changed = change(original)
        self.assertNotEqual(changed, original, "mutation did not apply")
        path.write_text(changed, encoding="utf-8")
        return self.errors()

    def assert_reported(self, errors: list[str], fragment: str) -> None:
        self.assertTrue(any(fragment in e for e in errors), f"{fragment!r} not in {errors}")

    def test_clean_copy_passes(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_read_only_agent_with_write_tool(self) -> None:
        errors = self.mutate(AGENT, lambda t: t.replace("tools: Read,", "tools: Edit, Read,"))
        self.assert_reported(errors, "must not have file-writing tools")

    def test_agent_relaxing_permission_mode(self) -> None:
        errors = self.mutate(AGENT, lambda t: t.replace("permissionMode: plan",
                                                        "permissionMode: bypassPermissions"))
        self.assert_reported(errors, "permissionMode must not relax approvals")

    def test_agent_with_unapproved_model(self) -> None:
        errors = self.mutate(AGENT, lambda t: t.replace("model: sonnet", "model: opus"))
        self.assert_reported(errors, "model must be one of")

    def test_agent_without_explicit_tools(self) -> None:
        errors = self.mutate(AGENT, lambda t: t.replace("tools: Read, Grep, Glob, Bash\n", ""))
        self.assert_reported(errors, "tools must be listed explicitly")

    def test_agent_with_nested_agents_or_mcp_tools(self) -> None:
        errors = self.mutate(AGENT, lambda t: t.replace(
            "tools: Read,", "tools: Agent, mcp__plugin_github_github__create_issue, Read,"))
        self.assert_reported(errors, "tools not allowed for project agents: Agent, mcp__")

    def test_agent_name_mismatch_and_missing_section(self) -> None:
        errors = self.mutate(AGENT, lambda t: t.replace("name: security-reviewer", "name: sec")
                             .replace("## Output Format", "## Output"))
        self.assert_reported(errors, "name must be kebab-case and match the file name")
        self.assert_reported(errors, "missing section '## Output Format'")

    def test_manual_skill_made_model_invocable(self) -> None:
        errors = self.mutate(SKILL, lambda t: t.replace("disable-model-invocation: true\n", ""))
        self.assert_reported(errors, "must set disable-model-invocation: true")

    def test_skill_pre_approving_unlisted_command(self) -> None:
        errors = self.mutate(SKILL, lambda t: t.replace(
            "disable-model-invocation: true", 'disable-model-invocation: true\n'
            'allowed-tools: "Bash(git push *) Read"'))
        self.assert_reported(errors, "allowed-tools broaden project permissions: Bash(git push *)")

    def test_skill_name_mismatch_and_missing_reference(self) -> None:
        errors = self.mutate(SKILL, lambda t: t.replace("name: prepare-commit", "name: commit")
                             + "\nSee `docs/MISSING.md`.\n")
        self.assert_reported(errors, "name must be kebab-case and match the directory name")
        self.assert_reported(errors, "references missing path docs/MISSING.md")

    def test_skill_directory_without_skill_file(self) -> None:
        (self.tmp / ".claude/skills/empty-skill").mkdir()
        self.assert_reported(self.errors(), ".claude/skills/empty-skill: SKILL.md is missing")


if __name__ == "__main__":
    unittest.main()
