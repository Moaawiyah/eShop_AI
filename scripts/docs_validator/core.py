"""Shared primitives for the documentation validator (standard library only)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

PRD_ID_DEFINITION = re.compile(r"^\| ((?:O|FR|NFR|AC|R|A|UD|PE)-[A-Z0-9-]+) \|", re.M)
PRD_REFERENCE = re.compile(r"\b(?:FR|NFR)-[A-Z]+-\d{3}\b|\bAC-\d{3}\b|\bUD-\d{2}\b")
TASK_REFERENCE = re.compile(r"\bSHOP-\d{3}\b")
ADR_REFERENCE = re.compile(r"\bADR-(\d{4})\b")


class ParseError(Exception):
    """A document is missing or does not have the expected structure."""


@dataclass
class Report:
    """Collected validation results."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, check: str, message: str) -> None:
        self.errors.append(f"[{check}] {message}")

    def warn(self, check: str, message: str) -> None:
        self.warnings.append(f"[{check}] {message}")

    def note(self, message: str) -> None:
        self.notes.append(message)


@dataclass
class Context:
    """Repository access plus facts shared between checks."""

    root: Path
    report: Report = field(default_factory=Report)
    prd_ids: set[str] = field(default_factory=set)
    task_ids: list[str] = field(default_factory=list)
    deps: dict[str, set[str]] = field(default_factory=dict)
    adr_numbers: list[str] = field(default_factory=list)
    _cache: dict[str, str] = field(default_factory=dict)

    def exists(self, relative: str) -> bool:
        return (self.root / relative).is_file()

    def text(self, relative: str) -> str:
        """Return a file's text; raise ParseError if it does not exist."""
        if relative not in self._cache:
            path = self.root / relative
            if not path.is_file():
                raise ParseError(f"required file {relative} is missing")
            self._cache[relative] = path.read_text(encoding="utf-8")
        return self._cache[relative]

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()


def between(text: str, start: str, end: str | None, *, where: str) -> str:
    """Return the text after ``start`` and before ``end`` (or the end of text)."""
    if start not in text:
        raise ParseError(f"{where}: marker {start!r} not found")
    after = text.split(start, 1)[1]
    if end is None:
        return after
    if end not in after:
        raise ParseError(f"{where}: marker {end!r} not found after {start!r}")
    return after.split(end, 1)[0]


def table_body(block: str) -> list[list[str]]:
    """Return the cells of a Markdown table's body rows (header and rule skipped)."""
    lines = [line for line in block.splitlines() if line.startswith("|")]
    rows = [line for line in lines[1:] if not re.fullmatch(r"\|[\s\-:|]+\|", line)]
    return [[cell.strip() for cell in row.strip("|").split("|")] for row in rows]


def split_list(cell: str) -> set[str]:
    """Split a comma-separated cell, ignoring parenthesized notes such as '(none)'."""
    return {item.strip() for item in cell.split(",") if item.strip() and "(" not in item}


def find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Return one dependency cycle as a path (first node repeated), or None."""
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        state[node] = 1
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if state.get(nxt) == 1:
                return stack[stack.index(nxt):] + [nxt]
            if nxt not in state:
                cycle = visit(nxt)
                if cycle:
                    return cycle
        state[node] = 2
        stack.pop()
        return None

    for start in sorted(graph):
        if start not in state:
            cycle = visit(start)
            if cycle:
                return cycle
    return None
