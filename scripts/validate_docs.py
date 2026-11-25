#!/usr/bin/env python3
"""Validate eShop_AI documentation and configuration consistency.

Read-only and standard library only. Checks PRD identifiers, roadmap tasks and
dependencies, delivery tiers, traceability, architecture dependency rules,
ADRs, cross-references, links, rule frontmatter, JSON configuration,
.env.example placeholders and machine-specific paths.

Usage (from any directory):
    python3 scripts/validate_docs.py [--root PATH] [--strict] [--quiet]

Exit codes: 0 no errors; 1 errors found (or warnings with --strict);
2 invalid arguments.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # also works under `python -I`

from docs_validator import run_all  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate eShop_AI documentation.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="repository root (default: the parent of scripts/)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--quiet", action="store_true", help="print only problems")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"--root {root} is not a directory")

    report = run_all(root)
    if not args.quiet:
        for note in report.notes:
            print(note)
    for warning in report.warnings:
        print(f"WARNING {warning}")
    for error in report.errors:
        print(f"ERROR   {error}")
    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    print(f"\n{'FAILED' if failed else 'PASSED'}: {len(report.errors)} error(s), "
          f"{len(report.warnings)} warning(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
