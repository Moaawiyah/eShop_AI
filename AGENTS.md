# eShop_AI — AI Agent Instructions

This file is the entry point for AI coding assistants other than Claude Code
(Claude Code loads `CLAUDE.md` directly). It adds no rules of its own beyond
the agent rules below and never overrides `CLAUDE.md`.

## 1. Read These Instructions

1. `CLAUDE.md` — primary engineering instructions, including instruction
   precedence (section 2), approval restrictions (section 12) and the Task
   Completion Report format (section 9).
2. The domain rule files in `.claude/rules/` that match the paths you work
   on. Claude Code loads them automatically using `paths:` frontmatter;
   other assistants must open them manually:

| Rule file | Read when working on |
|---|---|
| `.claude/rules/security.md` | Any task |
| `.claude/rules/testing.md` | `backend/`, `frontend/`, `services/`, `tests/` |
| `.claude/rules/backend.md` | `backend/` |
| `.claude/rules/frontend.md` | `frontend/` |
| `.claude/rules/integrations.md` | `backend/app/integrations/`, `backend/app/platform/` |
| `.claude/rules/ai-mcp.md` | `backend/app/modules/ai/`, `backend/app/integrations/llm/`, `backend/app/integrations/mcp/`, `services/ai/`, `tests/ai/` |
| `.claude/rules/devops.md` | `deployment/`, `monitoring/`, `scripts/`, `.github/`, Dockerfiles, Compose files |
| `.claude/rules/aws-infrastructure.md` | `infrastructure/`, Terraform files |

3. The project documents listed in `CLAUDE.md` section 8, limited to the
   sections relevant to the task.

## 2. Agent Rules

- Operate within the assigned task scope.
- Inspect existing code before modifying it.
- Respect accepted architectural decisions.
- Do not overwrite unrelated user changes.
- Report actual validation results only.
- Never expose credentials or secrets.
- Never perform any action listed in `CLAUDE.md` section 12 without
  explicit user approval.
- Record significant decisions as ADRs.
- Report conflicts between documents instead of resolving them silently.

## 3. Current Milestone

M0 — Project Initialization. Do not implement application features until
the project owner approves M1.
