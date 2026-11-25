"""Checks for project Claude Code subagents (.claude/agents) and skills (.claude/skills).

Enforces the project's least-privilege conventions on top of the documented
frontmatter format. Frontmatter is parsed as flat ``key: value`` lines, which is
the subset the project uses; anything else is reported instead of guessed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .core import Context, ParseError

NAME = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TOOL_ENTRY = re.compile(r"[A-Za-z_]+\([^)]*\)|[A-Za-z_][\w-]*")
PATH_REFERENCE = re.compile(r"`((?:docs|scripts|\.claude)/[^`*<>\s]+|[A-Z]+\.md)`")
AGENT_TOOLS = {"Read", "Grep", "Glob", "Edit", "Write", "Bash", "NotebookEdit", "LSP"}
AGENT_MODELS = {"sonnet", "haiku", "inherit"}  # Opus needs an explicit, reviewed exception.
AGENT_MODES = {"default", "manual", "plan"}
AGENT_SECTIONS = ("## Responsibilities", "## Required Context", "## Restrictions",
                  "## Output Format")
READ_ONLY_AGENTS = {"qa-engineer", "security-reviewer"}
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit"}
MANUAL_SKILLS = {"implement-task", "review-changes", "prepare-commit", "milestone-review",
                 "security-audit", "create-adr"}
SKILL_MODELS = {"haiku", "sonnet", "inherit"}
DESCRIPTION_LIMIT = 1536


def parse_frontmatter(text: str, label: str) -> tuple[dict[str, str], str]:
    """Return (fields, body); raise ParseError for missing or malformed frontmatter."""
    if not text.startswith("---\n"):
        raise ParseError(f"{label}: frontmatter must start on the first line")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise ParseError(f"{label}: frontmatter is not closed")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if not sep or not re.fullmatch(r"[a-zA-Z_-]+", key):
            raise ParseError(f"{label}: unsupported frontmatter line {line!r}")
        if key in fields:
            raise ParseError(f"{label}: duplicate frontmatter key {key}")
        fields[key] = value.strip().strip('"')
    return fields, text[end + 5:]


def _tools(value: str) -> list[str]:
    return TOOL_ENTRY.findall(value)


def _check_references(ctx: Context, label: str, body: str) -> None:
    for reference in PATH_REFERENCE.findall(body):
        if "NNN" in reference:
            continue  # template placeholder such as docs/adr/NNNN-short-title.md
        if not (ctx.root / reference.rstrip("/")).exists():
            ctx.report.error("claude config", f"{label}: references missing path {reference}")


def check_agents(ctx: Context) -> None:
    seen: set[str] = set()
    paths = sorted((ctx.root / ".claude/agents").glob("*.md"))
    for path in paths:
        label = ctx.rel(path)
        fields, body = parse_frontmatter(path.read_text(encoding="utf-8"), label)
        name = fields.get("name", "")
        problems: list[str] = []
        if not NAME.match(name) or name != path.stem:
            problems.append("name must be kebab-case and match the file name")
        if name in seen:
            problems.append(f"duplicate agent name {name}")
        seen.add(name)
        if len(fields.get("description", "")) < 60 or "Use " not in fields.get("description", ""):
            problems.append("description must state responsibilities and when to use it")
        tools = _tools(fields.get("tools", ""))
        if not tools:
            problems.append("tools must be listed explicitly (least privilege)")
        if unknown := sorted(set(tools) - AGENT_TOOLS):
            problems.append(f"tools not allowed for project agents: {', '.join(unknown)}")
        if name in READ_ONLY_AGENTS and WRITE_TOOLS & set(tools):
            problems.append("read-only agent must not have file-writing tools")
        if fields.get("model") not in AGENT_MODELS:
            problems.append(f"model must be one of {', '.join(sorted(AGENT_MODELS))}")
        if fields.get("permissionMode", "default") not in AGENT_MODES:
            problems.append("permissionMode must not relax approvals")
        problems += [f"missing section '{s}'" for s in AGENT_SECTIONS if s not in body]
        for problem in problems:
            ctx.report.error("claude config", f"{label}: {problem}")
        _check_references(ctx, label, body)
    ctx.report.note(f"Claude agents: {len(paths)} definitions")


def _settings_allow(ctx: Context) -> set[str]:
    path = ctx.root / ".claude/settings.json"
    if not path.is_file():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")).get("permissions", {})
               .get("allow", []))


def check_skills(ctx: Context) -> None:
    allowed = _settings_allow(ctx) | {"Read", "Grep", "Glob"}
    directories = sorted(p for p in (ctx.root / ".claude/skills").glob("*") if p.is_dir())
    for directory in directories:
        skill = directory / "SKILL.md"
        label = ctx.rel(skill)
        if not skill.is_file():
            ctx.report.error("claude config", f"{ctx.rel(directory)}: SKILL.md is missing")
            continue
        fields, body = parse_frontmatter(skill.read_text(encoding="utf-8"), label)
        problems: list[str] = []
        if fields.get("name") != directory.name or not NAME.match(directory.name):
            problems.append("name must be kebab-case and match the directory name")
        description = fields.get("description", "") + fields.get("when_to_use", "")
        if not description or len(description) > DESCRIPTION_LIMIT:
            problems.append(f"description must be 1 to {DESCRIPTION_LIMIT} characters")
        manual = fields.get("disable-model-invocation") == "true"
        if directory.name in MANUAL_SKILLS and not manual:
            problems.append("workflow skill must set disable-model-invocation: true")
        if broadened := sorted(set(_tools(fields.get("allowed-tools", ""))) - allowed):
            problems.append(f"allowed-tools broaden project permissions: {', '.join(broadened)}")
        if "model" in fields and fields["model"] not in SKILL_MODELS:
            problems.append(f"model must be one of {', '.join(sorted(SKILL_MODELS))}")
        if fields.get("context") == "fork" and not manual:
            problems.append("forked (subagent) skills must be manual-only")
        for problem in problems:
            ctx.report.error("claude config", f"{label}: {problem}")
        _check_references(ctx, label, body)
    ctx.report.note(f"Claude skills: {len(directories)} skills")


def claude_markdown_files(root: Path) -> list[Path]:
    return [*(root / ".claude/agents").glob("*.md"), *(root / ".claude/skills").glob("*/SKILL.md")]
