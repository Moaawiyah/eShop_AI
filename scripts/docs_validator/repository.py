"""Repository-wide checks: references, links, required documents and configuration."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .core import ADR_REFERENCE, PRD_REFERENCE, TASK_REFERENCE, Context

REQUIRED_DOCS = ("README.md", "AGENTS.md", "CONTRIBUTING.md", "docs/PRD.md",
                 "docs/ARCHITECTURE.md", "docs/ROADMAP.md", "docs/DEVELOPMENT.md",
                 "docs/SECURITY.md", "docs/DECISIONS.md")
PERSONAL_PATH = re.compile(r"/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Z]:\\Users\\")
SECRET_VALUE = re.compile(r"^(sk-|AKIA|ASIA|ghp_|gho_|github_pat_|xox[abp]-|AIza)"
                          r"|^[A-Za-z0-9+/_=-]{32,}$")
ENV_LINE = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")


def _markdown_files(ctx: Context) -> list[Path]:
    roots = [*ctx.root.glob("*.md"), *(ctx.root / "docs").rglob("*.md"),
             *(ctx.root / ".claude/rules").glob("*.md")]
    return sorted(set(roots))


def check_required_docs(ctx: Context) -> None:
    for relative in REQUIRED_DOCS:
        if not ctx.exists(relative):
            ctx.report.error("docs", f"required document {relative} is missing")
        elif not ctx.text(relative).strip():
            ctx.report.warn("docs", f"required document {relative} is empty")


def check_references(ctx: Context) -> None:
    """PRD IDs, roadmap tasks and ADR numbers referenced anywhere must exist."""
    files = _markdown_files(ctx)
    if ctx.exists(".env.example"):
        files.append(ctx.root / ".env.example")
    tasks, adrs = set(ctx.task_ids), set(ctx.adr_numbers)
    for path in files:
        text = path.read_text(encoding="utf-8")
        unknown = {
            "PRD IDs": sorted(set(PRD_REFERENCE.findall(text)) - ctx.prd_ids),
            "tasks": sorted(set(TASK_REFERENCE.findall(text)) - tasks),
            "ADRs": sorted(f"ADR-{n}" for n in set(ADR_REFERENCE.findall(text)) - adrs
                           if n != "0000"),
        }
        for label, items in unknown.items():
            if items:
                ctx.report.error("references", f"{ctx.rel(path)} references unknown {label}: {items}")


def check_links(ctx: Context) -> None:
    """Relative Markdown links point to existing files or directories."""
    count = 0
    for path in _markdown_files(ctx):
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            count += 1
            if not (path.parent / target.split("#", 1)[0]).exists():
                ctx.report.error("links", f"{ctx.rel(path)}: broken link {target}")
    ctx.report.note(f"Links: {count} relative links checked")


def check_rule_frontmatter(ctx: Context) -> None:
    for path in sorted((ctx.root / ".claude/rules").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue  # Rules without frontmatter are always loaded.
        frontmatter = text.split("---", 2)[1]
        if not re.search(r"^paths:\s*$", frontmatter, re.M) or not re.search(
                r'^\s+- "[^"]+"$', frontmatter, re.M):
            ctx.report.error("rules", f"{ctx.rel(path)}: malformed 'paths:' frontmatter")


def check_json_config(ctx: Context) -> None:
    for path in sorted((ctx.root / ".vscode").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            ctx.report.error("config", f"{ctx.rel(path)}: invalid JSON ({exc})")
            continue
        if path.name == "extensions.json" and not isinstance(data.get("recommendations"), list):
            ctx.report.error("config", f"{ctx.rel(path)}: 'recommendations' list missing")


def check_env_example(ctx: Context) -> None:
    """Keys well-formed and unique; values are placeholders, not credentials."""
    if not ctx.exists(".env.example"):
        ctx.report.error("env", ".env.example is missing")
        return
    seen: set[str] = set()
    for number, line in enumerate(ctx.text(".env.example").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = ENV_LINE.match(line)
        if not match:
            ctx.report.error("env", f".env.example line {number}: expected KEY=value")
            continue
        key, value = match.groups()
        if key in seen:
            ctx.report.error("env", f".env.example line {number}: duplicate key {key}")
        seen.add(key)
        if SECRET_VALUE.search(value) and "change-me" not in value:
            ctx.report.error("env", f".env.example line {number}: {key} looks like a real secret")
    ctx.report.note(f".env.example: {len(seen)} keys")


def check_personal_paths(ctx: Context) -> None:
    files = [*_markdown_files(ctx), *(ctx.root / ".vscode").glob("*.json")]
    if ctx.exists(".env.example"):
        files.append(ctx.root / ".env.example")
    for path in files:
        if PERSONAL_PATH.search(path.read_text(encoding="utf-8")):
            ctx.report.error("privacy", f"{ctx.rel(path)} contains a machine-specific path")
