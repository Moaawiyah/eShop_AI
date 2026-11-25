"""Checks for architecture dependency rules and Architecture Decision Records."""

from __future__ import annotations

import re

from .core import Context, between, find_cycle, split_list, table_body

ARCHITECTURE = "docs/ARCHITECTURE.md"
DECISIONS = "docs/DECISIONS.md"
ADR_STATUSES = {"Proposed", "Accepted", "Superseded", "Deprecated"}
ADR_SECTIONS = ("## Context", "## Decision", "## Alternatives Considered", "## Consequences",
                "**Positive**", "**Negative**", "## Related Requirements and Tasks",
                "## Reconsideration Conditions")


def check_dependency_rules(ctx: Context) -> None:
    """Package and module dependency tables are acyclic and match the module diagram."""
    arch = ctx.text(ARCHITECTURE)
    packages = {row[0]: split_list(row[1]) for row in table_body(
        "| Package |" + between(arch, "| Package | May depend on |", "\n\n", where=ARCHITECTURE))}
    unknown = sorted({d for deps in packages.values() for d in deps} - set(packages))
    if unknown:
        ctx.report.error("architecture", f"package table names unknown packages: {unknown}")
    if cycle := find_cycle(packages):
        ctx.report.error("architecture", f"package dependency cycle: {' -> '.join(cycle)}")

    header = "| Module | Responsibility | Owns data | Calls modules |"
    modules = {row[0]: split_list(row[3]) for row in table_body(
        header + between(arch, header, "\n\n", where=ARCHITECTURE))}
    if cycle := find_cycle(modules):
        ctx.report.error("architecture", f"module dependency cycle: {' -> '.join(cycle)}")
    diagram = between(between(arch, "Domain module dependencies", None, where=ARCHITECTURE),
                      "```mermaid", "```", where=f"{ARCHITECTURE} module diagram")
    edges = set(re.findall(r"(\w+)(?:\[[^\]]*\])?(?::::\w+)? --> (\w+)", diagram))
    table_edges = {(a, b) for a, deps in modules.items() for b in deps}
    if edges != table_edges:
        ctx.report.error("architecture",
                         f"module diagram and table differ: {sorted(edges ^ table_edges)}")
    ctx.report.note(f"Architecture: {len(packages)} packages, {len(modules)} modules, "
                    f"{arch.count('```mermaid')} Mermaid diagrams")


def check_adrs(ctx: Context) -> None:
    """ADR numbering, headings, required sections and index consistency."""
    adr_dir = ctx.root / "docs/adr"
    files = sorted(adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"))
    numbers = [f.name[:4] for f in files]
    if numbers != [f"{i:04d}" for i in range(1, len(numbers) + 1)]:
        ctx.report.error("adr", f"ADR numbers are not unique and sequential: {numbers}")
    if not (adr_dir / "template.md").is_file():
        ctx.report.error("adr", "docs/adr/template.md is missing")
    index = ctx.text(DECISIONS)
    for path in files:
        name, text = path.name, path.read_text(encoding="utf-8")
        heading = re.match(r"# ADR-(\d{4}): \S", text)
        if not heading or heading.group(1) != name[:4]:
            ctx.report.error("adr", f"{name}: first line must be '# ADR-{name[:4]}: <title>'")
        for section in ADR_SECTIONS:
            if section not in text:
                ctx.report.error("adr", f"{name}: missing section {section!r}")
        status = re.search(r"^\| Status \| (\w+)", text, re.M)
        if not status or status.group(1) not in ADR_STATUSES:
            ctx.report.error("adr", f"{name}: status must be one of {sorted(ADR_STATUSES)}")
            continue
        row = re.search(rf"^\| \[ADR-{name[:4]}\]\(adr/{re.escape(name)}\) \| .+? \| (\w+)",
                        index, re.M)
        if not row:
            ctx.report.error("adr", f"{name}: not indexed in {DECISIONS}")
        elif row.group(1) != status.group(1):
            ctx.report.error("adr", f"{name}: status {status.group(1)} but {DECISIONS} "
                                    f"says {row.group(1)}")
    ctx.adr_numbers = numbers
    ctx.report.note(f"ADRs: {len(files)} records")
