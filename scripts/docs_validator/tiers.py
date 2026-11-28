"""Checks for roadmap delivery tiers and the Tier 1 estimate."""

from __future__ import annotations

import re

from .core import Context, between

ROADMAP = "docs/ROADMAP.md"


def tier_assignments(ctx: Context) -> dict[str, list[tuple[str, int]]]:
    """Map each task to its (milestone, tier) entries in the section 2.2 tier table."""
    block = between(ctx.text(ROADMAP), "### 2.2 Portfolio Delivery Tiers", "### 2.3",
                    where=ROADMAP)
    found: dict[str, list[tuple[str, int]]] = {}
    for line in block.splitlines():
        match = re.match(r"^\| (M\d+|Backlog) \|", line)
        if match:
            cells = [c.strip() for c in line.split("|")[2:5]]
            for tier, cell in enumerate(cells, start=1):
                for number in re.findall(r"\d{3}", cell):
                    found.setdefault(f"SHOP-{number}", []).append((match.group(1), tier))
    return found


def check_tiers(ctx: Context) -> None:
    """Every task is in exactly one tier; no task depends on a later tier."""
    tiers = {task: [tier for _, tier in entries]
             for task, entries in tier_assignments(ctx).items()}
    ids = set(ctx.task_ids)
    problems = {
        "assigned to several tiers": sorted(t for t, v in tiers.items() if len(v) > 1),
        "without a tier": sorted(ids - set(tiers)),
        "in the tier table but not in the backlog": sorted(set(tiers) - ids),
    }
    for label, tasks in problems.items():
        if tasks:
            ctx.report.error("tiers", f"tasks {label}: {tasks}")
    for task, deps in sorted(ctx.deps.items()):
        tier = tiers.get(task, [0])[0]
        for dep in sorted(deps):
            dep_tier = tiers.get(dep, [0])[0]
            if dep_tier > tier:
                ctx.report.error("tiers", f"{task} (tier {tier}) depends on {dep} (tier {dep_tier})")
    counts = {n: sum(1 for v in tiers.values() if v[0] == n) for n in (1, 2, 3)}
    ctx.report.note(f"Tiers: {counts[1]} essential, {counts[2]} advanced, {counts[3]} optional")


def check_tier1_estimate(ctx: Context) -> None:
    """Weekly plan, stated total and per-milestone totals agree."""
    plan = between(ctx.text(ROADMAP), "### 2.3", "### 2.4", where=ROADMAP)
    weeks = [float(x) for x in re.findall(r"^\| \d+ \|.*\| ([\d.]+) \|$", plan, re.M)]
    total_match = re.search(r"\| \*\*Total\*\* \| \| \*\*([\d.]+)\*\* \|", plan)
    per_milestone = between(plan, "Per-milestone", "\n\n", where=f"{ROADMAP} section 2.3")
    milestones = [float(x) for x in re.findall(r"M\d+ (\d+(?:\.\d+)?)", per_milestone)]
    if not total_match or not weeks or not milestones:
        ctx.report.error("estimate", "Tier 1 plan table or per-milestone totals not found")
        return
    stated = float(total_match.group(1))
    if abs(sum(weeks) - stated) > 1e-9 or abs(sum(milestones) - stated) > 1e-9:
        ctx.report.error("estimate", f"Tier 1 totals disagree: weeks {sum(weeks)}, "
                                     f"stated {stated}, milestones {sum(milestones)}")
    ctx.report.note(f"Tier 1 estimate: {stated} days over {len(weeks)} weeks")
