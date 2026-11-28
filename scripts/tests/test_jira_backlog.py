"""Mutation tests for the Jira import files check (docs/jira/, SHOP-009).

Each test changes one value in a temporary copy of the documentation and
expects the validator to report it. The real repository is never modified.

Run: python3 -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import unittest

from test_validate_docs import MutationCase

BACKLOG = "docs/jira/backlog.csv"
ISSUE_MAP = "docs/jira/issue-map.csv"
ROW_010 = "SHOP-010,SHOP-010 Backend skeleton,Task,To Do,Highest,M1,mvp,backend,tier-1,,57600,"


class JiraBacklogTests(MutationCase):
    def test_priority_must_match_roadmap(self) -> None:
        self.mutate(BACKLOG, ROW_010, ROW_010.replace(",Highest,", ",High,"))
        self.assert_reported("SHOP-010: priority High differs from the roadmap (Highest)")

    def test_milestone_and_tier_must_match(self) -> None:
        self.mutate(BACKLOG, ",M2,mvp,testing,tier-2,", ",M1,mvp,testing,tier-1,")
        self.assert_reported("SHOP-028: Fix Version M1 differs from the tier table (M2)")
        self.assert_reported("SHOP-028: labels mvp/tier-1 differ from track MVP and tier 2")

    def test_estimate_and_dependencies_must_match(self) -> None:
        self.mutate(BACKLOG, ROW_010 + '"Roadmap ID SHOP-010. Depends on: SHOP-008.',
                    ROW_010.replace(",57600,", ",28800,")
                    + '"Roadmap ID SHOP-010. Depends on: SHOP-009.')
        self.assert_reported("SHOP-010: estimate differs from 2 ideal days")
        self.assert_reported("SHOP-010: dependencies differ from the roadmap (SHOP-008)")

    def test_done_status_must_match_roadmap(self) -> None:
        self.mutate(BACKLOG, "SHOP-009 Jira project setup and backlog import,Task,To Do,",
                    "SHOP-009 Jira project setup and backlog import,Task,Done,")
        self.assert_reported("SHOP-009: status disagrees with the roadmap")

    def test_duplicate_and_unknown_rows(self) -> None:
        with (self.root / BACKLOG).open("a", encoding="utf-8") as backlog:
            backlog.write(ROW_010 + '"Roadmap ID SHOP-010. Depends on: SHOP-008."\n')
            backlog.write(ROW_010.replace("SHOP-010", "SHOP-999") + '"x"\n')
        self.assert_reported("duplicate roadmap ID SHOP-010")
        self.assert_reported("unknown roadmap ID SHOP-999")

    def test_issue_map_rejects_duplicates_and_gaps(self) -> None:
        self.mutate(ISSUE_MAP, "SHOP-001,\nSHOP-002,\n", "SHOP-001,ESHOP-1\nSHOP-002,ESHOP-1\n")
        self.mutate(ISSUE_MAP, "SHOP-003,\n", "SHOP-003,SHOP-30\n")
        self.mutate(ISSUE_MAP, "SHOP-125,\n", "")
        self.assert_reported("duplicate Jira keys: ['ESHOP-1']")
        self.assert_reported("malformed Jira keys: ['SHOP-30']")
        self.assert_reported("backlog rows missing from the map: ['SHOP-125']")


if __name__ == "__main__":
    unittest.main()
