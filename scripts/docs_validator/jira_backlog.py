"""Checks for the Jira import files in docs/jira/ (SHOP-009, roadmap section 10).

Roadmap IDs are the permanent identifiers; Jira generates its own keys. The
backlog must preserve the roadmap's priority, milestone, tier, track, estimate,
dependencies and status, and the issue map must not allow duplicates.
"""

from __future__ import annotations

import csv
import re
from collections import Counter

from .core import Context
from .prd_roadmap import ROADMAP, TASK_ROW
from .tiers import tier_assignments

BACKLOG = "docs/jira/backlog.csv"
ISSUE_MAP = "docs/jira/issue-map.csv"
HEADER = ["Roadmap ID", "Summary", "Issue Type", "Status", "Priority", "Fix Version", "Labels",
          "Labels", "Labels", "Labels", "Original Estimate", "Description"]
STATUSES = {"To Do", "In Progress", "In Review", "Done", "Blocked"}
AREAS = {"docs", "backend", "frontend", "ai", "devops", "aws", "security", "testing"}
SECONDS_PER_DAY = 8 * 3600
JIRA_KEY = re.compile(r"ESHOP-[1-9]\d*")  # PRD A-05


def _rows(ctx: Context, relative: str) -> list[list[str]]:
    with (ctx.root / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def _row_problems(row: list[str], task: list[str], placement: tuple[str, int]) -> list[str]:
    """Differences between one backlog row and its roadmap task row and tier."""
    rid, summary, _, status, priority, fix_version = row[:6]
    track, area, tier, state = row[6:10]
    milestone, tier_number = placement
    deps = sorted(re.findall(r"SHOP-\d{3}", task[4]))
    listed = re.search(r"Depends on: ([^.]*)\.", row[11])
    problems = {
        "summary must start with the roadmap ID": not summary.startswith(rid + " "),
        f"unknown status {status!r}": status not in STATUSES,
        f"priority {priority} differs from the roadmap ({task[2]})": priority != task[2],
        f"Fix Version {fix_version} differs from the tier table ({milestone})":
            fix_version != milestone,
        f"labels {track}/{tier} differ from track {task[1]} and tier {tier_number}":
            track != task[1].lower() or tier != f"tier-{tier_number}",
        f"unknown area label {area!r}": area not in AREAS,
        f"unknown state label {state!r}": state not in ("", "deferred"),
        f"estimate differs from {task[3]} ideal days":
            row[10] != str(round(float(task[3]) * SECONDS_PER_DAY)),
        f"dependencies differ from the roadmap ({', '.join(deps) or 'none'})":
            not listed or sorted(re.findall(r"SHOP-\d{3}", listed.group(1))) != deps,
    }
    if len(task) > 5 and task[5]:  # milestone tables with a Status column (M0)
        problems["status disagrees with the roadmap"] = (
            (status == "Done") != task[5].startswith("Done"))
    return [message for message, failed in problems.items() if failed]


def check_jira_backlog(ctx: Context) -> None:
    rows = _rows(ctx, BACKLOG)
    if not rows or rows[0] != HEADER:
        ctx.report.error("jira", f"{BACKLOG}: header must be {','.join(HEADER)}")
        return
    tasks = {tid: [c.strip() for c in rest.split("|")]
             for tid, rest in TASK_ROW.findall(ctx.text(ROADMAP))}
    placements = tier_assignments(ctx)
    ids = [row[0] for row in rows[1:]]
    for rid in sorted(i for i, n in Counter(ids).items() if n > 1):
        ctx.report.error("jira", f"{BACKLOG}: duplicate roadmap ID {rid}")
    for number, row in enumerate(rows[1:], start=2):
        if len(row) != len(HEADER):
            ctx.report.error("jira", f"{BACKLOG} line {number}: expected {len(HEADER)} columns")
        elif row[0] not in tasks or row[0] not in placements:
            ctx.report.error("jira", f"{BACKLOG} line {number}: unknown roadmap ID {row[0]}")
        else:
            for problem in _row_problems(row, tasks[row[0]], placements[row[0]][0]):
                ctx.report.error("jira", f"{BACKLOG} {row[0]}: {problem}")
    ctx.report.note(f"Jira backlog: {len(ids)} rows")
    _check_issue_map(ctx, set(ids))


def _check_issue_map(ctx: Context, backlog_ids: set[str]) -> None:
    rows = _rows(ctx, ISSUE_MAP)
    if not rows or rows[0] != ["Roadmap ID", "Jira Key"]:
        ctx.report.error("jira", f"{ISSUE_MAP}: header must be Roadmap ID,Jira Key")
        return
    entries = [row for row in rows[1:] if row]
    ids = [row[0] for row in entries]
    keys = [row[1] for row in entries if len(row) > 1 and row[1]]
    checks = {
        "duplicate roadmap IDs": [i for i, n in Counter(ids).items() if n > 1],
        "duplicate Jira keys": [k for k, n in Counter(keys).items() if n > 1],
        "malformed Jira keys": [k for k in keys if not JIRA_KEY.fullmatch(k)],
        "roadmap IDs not in the backlog": sorted(set(ids) - backlog_ids),
        "backlog rows missing from the map": sorted(backlog_ids - set(ids)),
    }
    for label, items in checks.items():
        if items:
            ctx.report.error("jira", f"{ISSUE_MAP}: {label}: {sorted(items)}")
    ctx.report.note(f"Jira issue map: {len(keys)}/{len(ids)} mapped")
