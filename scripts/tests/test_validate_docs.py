"""Self-tests for scripts/validate_docs.py (standard library unittest).

Run from the repository root:
    python3 -m unittest discover -s scripts/tests -v

Mutation tests copy the documentation into a temporary directory, introduce
one defect and assert that the validator reports it. The real repository is
never modified.
"""

from __future__ import annotations

import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import validate_docs  # noqa: E402
from docs_validator import run_all  # noqa: E402
from docs_validator.core import find_cycle, split_list, table_body  # noqa: E402

COPIED = ("README.md", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", ".env.example")


class HelperTests(unittest.TestCase):
    def test_find_cycle_reports_cycle(self) -> None:
        self.assertEqual(find_cycle({"a": {"b"}, "b": {"a"}}), ["a", "b", "a"])

    def test_find_cycle_accepts_acyclic_graph(self) -> None:
        self.assertIsNone(find_cycle({"a": {"b", "c"}, "b": {"c"}, "c": set()}))

    def test_split_list_ignores_notes(self) -> None:
        self.assertEqual(split_list("core, database"), {"core", "database"})
        self.assertEqual(split_list("(none)"), set())

    def test_table_body_skips_header_and_rule(self) -> None:
        self.assertEqual(table_body("| A | B |\n|---|---|\n| 1 | 2 |"), [["1", "2"]])


class RepositoryTests(unittest.TestCase):
    def test_repository_has_no_errors(self) -> None:
        self.assertEqual(run_all(REPO).errors, [])

    @unittest.skipIf(shutil.which("git") is None, "git not available")
    def test_env_files_ignored_but_example_tracked(self) -> None:
        def git(*args: str) -> int:
            return subprocess.run(["git", "-C", str(REPO), *args],
                                  capture_output=True, check=False).returncode

        if git("rev-parse", "--is-inside-work-tree") != 0:
            self.skipTest("not a git work tree")
        for name in (".env", ".env.local", ".env.production"):
            self.assertEqual(git("check-ignore", "-q", name), 0, f"{name} must be ignored")
        for name in (".env.example", ".vscode/settings.json", ".vscode/extensions.json"):
            self.assertEqual(git("check-ignore", "-q", name), 1, f"{name} must not be ignored")
        self.assertEqual(git("ls-files", "--error-unmatch", ".env.example"), 0)


class MutationTests(unittest.TestCase):
    """Each test plants one defect in a temporary copy and expects it reported."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for name in COPIED:
            shutil.copy2(REPO / name, self.root / name)
        for folder in ("docs", ".claude/rules", ".vscode"):
            shutil.copytree(REPO / folder, self.root / folder)
        (self.root / "README.md").write_text("# eShop_AI\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def mutate(self, relative: str, old: str, new: str) -> None:
        path = self.root / relative
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count(old), 1, f"mutation anchor not unique in {relative}")
        path.write_text(text.replace(old, new), encoding="utf-8")

    def assert_reported(self, fragment: str) -> None:
        errors = run_all(self.root).errors
        self.assertTrue(any(fragment in e for e in errors), f"{fragment!r} not in {errors}")

    def test_clean_copy_passes_strict(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validate_docs.main(["--root", str(self.root), "--strict"]), 0)

    def test_empty_required_document_is_warning_and_fails_strict(self) -> None:
        (self.root / "README.md").write_text("", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validate_docs.main(["--root", str(self.root)]), 0)
            self.assertEqual(validate_docs.main(["--root", str(self.root), "--strict"]), 1)

    def test_missing_required_document(self) -> None:
        (self.root / "docs/SECURITY.md").unlink()
        self.assert_reported("required document docs/SECURITY.md is missing")

    def test_unknown_prd_id(self) -> None:
        self.mutate("docs/adr/0003-internal-sdk-and-provider-abstraction.md",
                    "FR-PLAT-001,", "FR-PLAT-099,")
        self.assert_reported("unknown PRD IDs: ['FR-PLAT-099']")

    def test_unknown_task(self) -> None:
        self.mutate("docs/DECISIONS.md", "| UD-07 | Search implementation | SHOP-021 |",
                    "| UD-07 | Search implementation | SHOP-321 |")
        self.assert_reported("unknown tasks: ['SHOP-321']")

    def test_dependency_cycle(self) -> None:
        self.mutate("docs/ROADMAP.md", "| MVP | High | 1 | SHOP-010, SHOP-014 |",
                    "| MVP | High | 1 | SHOP-010, SHOP-014, SHOP-022 |")
        self.assert_reported("dependency cycle")

    def test_tier_violation(self) -> None:
        self.mutate("docs/ROADMAP.md", "| M5 | 053, 054 | 051,", "| M5 | 054 | 053, 051,")
        self.assert_reported("(tier 1) depends on SHOP-053 (tier 2)")

    def test_estimate_mismatch(self) -> None:
        self.mutate("docs/ROADMAP.md", "| 6 | M4 back office | 040–045 | 5.25 |",
                    "| 6 | M4 back office | 040–045 | 5 |")
        self.assert_reported("Tier 1 totals disagree")

    def test_module_cycle(self) -> None:
        self.mutate("docs/ARCHITECTURE.md", "| simulated_payments | (none) |",
                    "| simulated_payments | orders |")
        self.assert_reported("module dependency cycle")

    def test_adr_index_status_mismatch(self) -> None:
        self.mutate("docs/DECISIONS.md", "with CSRF protection | Accepted",
                    "with CSRF protection | Proposed")
        self.assert_reported("0004-cookie-sessions-and-csrf.md: status Accepted")

    def test_adr_missing_section(self) -> None:
        self.mutate("docs/adr/0005-integer-cents-usd.md", "## Reconsideration Conditions",
                    "## Later")
        self.assert_reported("missing section '## Reconsideration Conditions'")

    def test_broken_link(self) -> None:
        self.mutate("CONTRIBUTING.md", "(docs/SECURITY.md)", "(docs/SECURE.md)")
        self.assert_reported("broken link docs/SECURE.md")

    def test_invalid_json(self) -> None:
        (self.root / ".vscode/settings.json").write_text("{ invalid", encoding="utf-8")
        self.assert_reported(".vscode/settings.json: invalid JSON")

    def test_env_duplicate_key_and_secret(self) -> None:
        with (self.root / ".env.example").open("a", encoding="utf-8") as env:
            env.write("APP_ENV=test\nLLM_API_KEY=sk-live0123456789\n")
        self.assert_reported("duplicate key APP_ENV")
        self.assert_reported("LLM_API_KEY looks like a real secret")

    def test_personal_path(self) -> None:
        with (self.root / "docs/DEVELOPMENT.md").open("a", encoding="utf-8") as doc:
            doc.write("\nSee /Users/someone/project.\n")
        self.assert_reported("docs/DEVELOPMENT.md contains a machine-specific path")


if __name__ == "__main__":
    unittest.main()
