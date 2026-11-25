"""Checks for the PRD and the roadmap task backlog."""

from __future__ import annotations

import csv
import io
import re
from collections import Counter

from .core import PRD_ID_DEFINITION, Context, between, find_cycle

PRD = "docs/PRD.md"
ROADMAP = "docs/ROADMAP.md"
TASK_ROW = re.compile(r"^\| (SHOP-\d{3}) \|(.*)$", re.M)


def check_prd_ids(ctx: Context) -> None:
    prd = ctx.text(PRD)
    defined = PRD_ID_DEFINITION.findall(prd)
    duplicates = sorted(i for i, n in Counter(defined).items() if n > 1)
    if duplicates:
        ctx.report.error("prd", f"{PRD} defines duplicate IDs: {duplicates}")
    ctx.prd_ids = set(defined)
    sections = [int(n) for n in re.findall(r"^## (\d+)\. ", prd, re.M)]
    if sections != list(range(1, len(sections) + 1)):
        ctx.report.error("prd", f"{PRD} numbered sections are not sequential: {sections}")
    ctx.report.note(f"PRD: {len(defined)} defined IDs, {len(sections)} numbered sections")


def check_tasks(ctx: Context) -> None:
    """Task IDs unique and sequential; dependencies exist, point backwards, no cycles."""
    rows = TASK_ROW.findall(ctx.text(ROADMAP))
    ids = [tid for tid, _ in rows]
    duplicates = sorted(i for i, n in Counter(ids).items() if n > 1)
    if duplicates:
        ctx.report.error("tasks", f"duplicate task rows: {duplicates}")
    numbers = sorted({int(i[5:]) for i in ids})
    if numbers != list(range(1, len(numbers) + 1)):
        ctx.report.error("tasks", "task IDs are not sequential from SHOP-001")
    # Tasks appended after the original numbering may be depended on "forward".
    appended = {tid for tid, rest in rows if re.search(r"added in SHOP-\d{3}", rest)}
    deps: dict[str, set[str]] = {}
    for tid, rest in rows:
        cells = [c.strip() for c in rest.split("|")]
        deps[tid] = set(re.findall(r"SHOP-\d{3}", cells[4] if len(cells) > 4 else ""))
        for dep in sorted(deps[tid]):
            if dep not in ids:
                ctx.report.error("tasks", f"{tid} depends on unknown task {dep}")
            elif dep == tid:
                ctx.report.error("tasks", f"{tid} depends on itself")
            elif int(dep[5:]) > int(tid[5:]) and dep not in appended:
                ctx.report.error("tasks", f"{tid} has a forward dependency on {dep}")
    cycle = find_cycle(deps)
    if cycle:
        ctx.report.error("tasks", f"dependency cycle: {' -> '.join(cycle)}")
    ctx.task_ids, ctx.deps = ids, deps
    if numbers:
        ctx.report.note(f"Roadmap: {len(ids)} tasks (SHOP-001..SHOP-{numbers[-1]:03d})")


def check_mermaid_task_nodes(ctx: Context) -> None:
    for node, label in set(re.findall(r'S(\d{3})\["SHOP-(\d{3})', ctx.text(ROADMAP))):
        if node != label or f"SHOP-{node}" not in ctx.task_ids:
            ctx.report.error("mermaid", f"node S{node} is labelled SHOP-{label}")


def _expand_requirement_cell(cell: str, known: set[str]) -> set[str]:
    """Expand 'FR-X-001 to 003, 005' and prefix-only tokens like 'NFR-USE'."""
    covered: set[str] = set()
    prefix, last = "", 0
    for token in re.findall(r"(?:FR|NFR)-[A-Z]+(?:-\d{3})?|to \d{3}|\d{3}", cell):
        if re.fullmatch(r"(?:FR|NFR)-[A-Z]+-\d{3}", token):
            prefix, last = token[:-4], int(token[-3:])
            covered.add(token)
        elif re.fullmatch(r"(?:FR|NFR)-[A-Z]+", token):
            covered.update(i for i in known if i.startswith(token + "-"))
        elif token.startswith("to ") and prefix:
            end = int(token[3:])
            covered.update(f"{prefix}-{n:03d}" for n in range(last, end + 1))
            last = end
        elif prefix:
            last = int(token)
            covered.add(f"{prefix}-{last:03d}")
    return covered


def check_traceability(ctx: Context) -> None:
    matrix = between(ctx.text(ROADMAP), "## 9. Requirement-to-Milestone Traceability Matrix",
                     "## 10.", where=ROADMAP)
    covered: set[str] = set()
    for line in matrix.splitlines():
        if line.startswith("| ") and not line.startswith("| PRD"):
            covered |= _expand_requirement_cell(line.split("|")[1], ctx.prd_ids)
    requirements = {i for i in ctx.prd_ids if i.startswith(("FR-", "NFR-"))}
    missing = sorted(requirements - covered)
    if missing:
        ctx.report.error("traceability", f"requirements not in the matrix: {missing}")
    ctx.report.note(f"Traceability: {len(requirements & covered)}/{len(requirements)} mapped")


def check_jira_csv(ctx: Context) -> None:
    block = between(ctx.text(ROADMAP), "```csv", "```", where=ROADMAP).strip()
    rows = list(csv.reader(io.StringIO(block)))
    widths = {len(r) for r in rows}
    if len(widths) != 1:
        ctx.report.error("csv", f"Jira CSV rows have inconsistent column counts: {widths}")
    ctx.report.note(f"Jira CSV: {len(rows) - 1} rows")
