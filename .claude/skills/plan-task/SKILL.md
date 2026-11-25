---
name: plan-task
description: "Produce an implementation plan for one eShop_AI roadmap task (SHOP-NNN): scope, dependencies, PRD requirements, acceptance criteria, affected files, risks and validation. Use when the user asks to plan, scope or estimate a SHOP task. Read-only."
argument-hint: "SHOP-NNN"
---

# Plan a SHOP Task

Plan task **$ARGUMENTS**. Do not create or modify any file.

1. **Locate the task.** Find its row in `docs/ROADMAP.md` (section 7) and
   its Jira CSV row (section 10; M0 to M2 only). Stop and report if the ID is missing or
   malformed.
2. **Check readiness.** For each dependency, report its status. Confirm the
   task's milestone is the current one in `CLAUDE.md` section 1; if not,
   say that the plan needs owner approval to start early.
3. **Collect requirements.** Read only the PRD requirement IDs the task cites
   (`docs/PRD.md`) and any acceptance criteria (PRD section 19) they map to.
   Note accepted ADRs, architecture sections and scoped rules that apply.
4. **Inspect existing files** with focused searches; list what exists, what
   must change and what is new.
5. **Identify risks and decisions**: unresolved decisions (UD-NN), new
   dependencies, security impact, actions requiring approval under
   `CLAUDE.md` section 12.

## Output

- Objective (one sentence), tier and estimate from the roadmap.
- Dependencies with status; blockers first.
- Requirements and acceptance criteria to satisfy.
- Implementation steps (small, ordered, each with target files).
- Tests to add (success and failure paths) and validation commands.
- Approvals needed, open questions and a suggested specialist agent only
  if one would clearly help.
- Suggested branch name `<prefix>/SHOP-NNN-<short-name>` (`CLAUDE.md` section 10).
