---
name: milestone-review
description: "Assess whether an eShop_AI milestone (M0 to M11) meets its exit criteria: task status, evidence, incomplete or blocked items and a readiness verdict for the project owner. Manual invocation only; never advances the milestone."
argument-hint: "M<number>"
disable-model-invocation: true
---

# Milestone Review

Review milestone **$ARGUMENTS** (default: the current milestone in
`CLAUDE.md` section 1). Do not change any status or file.

1. **Read the milestone** in `docs/ROADMAP.md` section 7: objective, tasks,
   required tests, security and cost considerations, additional Definition
   of Done and exit criteria; plus the Global Definition of Done (section 6).
2. **Check each task**: roadmap status, delivered artifacts present in the
   repository, evidence (commits referencing the key via
   `git log --oneline --grep <key>`, validation results, documents).
   Flag tasks marked Done without evidence and evidence without a status update.
3. **Run deterministic checks** that exist (`/validate-project` for the
   relevant scope). Do not install tools.
4. **Check open decisions** in `docs/DECISIONS.md` and PRD section 20 that
   the milestone was meant to resolve, and approvals still required under
   `CLAUDE.md` section 12.

## Output

- Verdict: **Ready for owner approval**, **Ready after listed items**, or
  **Not ready**.
- Table: task, status, evidence, gap.
- Exit criteria checklist with met, not met or needs owner judgment.
- Blockers, risks and the smallest set of actions to reach readiness.

Advancing the milestone in `CLAUDE.md` and `docs/ROADMAP.md` requires the
project owner's explicit approval in a separate request.
