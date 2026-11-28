"""Read-only consistency checks for eShop_AI documentation and configuration."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from . import architecture_adrs, claude_config, jira_backlog, prd_roadmap, repository, tiers
from .core import Context, ParseError, Report

Check = Callable[[Context], None]

# Order matters: later checks use facts (IDs, tasks, ADR numbers) gathered earlier.
CHECKS: tuple[tuple[str, Check], ...] = (
    ("required documents", repository.check_required_docs),
    ("PRD identifiers", prd_roadmap.check_prd_ids),
    ("roadmap tasks", prd_roadmap.check_tasks),
    ("roadmap Mermaid nodes", prd_roadmap.check_mermaid_task_nodes),
    ("traceability matrix", prd_roadmap.check_traceability),
    ("Jira backlog", jira_backlog.check_jira_backlog),
    ("delivery tiers", tiers.check_tiers),
    ("Tier 1 estimate", tiers.check_tier1_estimate),
    ("architecture dependencies", architecture_adrs.check_dependency_rules),
    ("ADRs", architecture_adrs.check_adrs),
    ("cross-references", repository.check_references),
    ("Markdown links", repository.check_links),
    ("rule frontmatter", repository.check_rule_frontmatter),
    ("JSON configuration", repository.check_json_config),
    (".env.example", repository.check_env_example),
    ("personal paths", repository.check_personal_paths),
    ("Claude agents", claude_config.check_agents),
    ("Claude skills", claude_config.check_skills),
)


def run_all(root: Path) -> Report:
    """Run every check against the repository at ``root``; never modifies files."""
    ctx = Context(root=root)
    for name, check in CHECKS:
        try:
            check(ctx)
        except ParseError as exc:
            ctx.report.error(name, str(exc))
        except Exception as exc:  # A broken check must fail loudly, not pass silently.
            ctx.report.error(name, f"check could not complete: {type(exc).__name__}: {exc}")
    return ctx.report


__all__ = ["CHECKS", "Report", "run_all"]
