---
name: implement-task
description: "Implement an approved eShop_AI SHOP task with tests and focused validation, then report actual results. Manual invocation only; never commits or pushes."
argument-hint: "SHOP-NNN"
disable-model-invocation: true
---

# Implement a SHOP Task

Implement task **$ARGUMENTS**.

1. **Confirm scope.** Use the plan approved in this conversation; if none
   exists, run the planning steps of `/plan-task` and ask for approval
   before editing. Confirm prerequisites are done and the work fits the
   current milestone (`CLAUDE.md` section 1).
2. **Check the branch.** Work on `<prefix>/SHOP-NNN-<short-name>`. If you are
   on `main` or another task's branch, ask before creating or switching.
3. **Implement** the smallest change that meets the acceptance criteria,
   following existing conventions and the scoped rules for each path.
   Delegate to one specialist agent (`backend-engineer`,
   `frontend-engineer`, `devops-engineer`, `ai-engineer`) only when the task
   is large or specialised enough to benefit; give it the approved plan and
   explicit file scope. Do not run several agents by default.
4. **Test** successful and unsuccessful paths. Never weaken or delete tests.
5. **Validate** with the targeted checks from `/validate-project` for the
   changed components. Fix failures caused by the change.
6. **Update documentation** affected by the change, including the task
   status in `docs/ROADMAP.md` when the owner confirms completion.
7. **Stop before Git.** Do not stage, commit or push; suggest `/prepare-commit`.

## Output

The Task Completion Report from `CLAUDE.md` section 9, with every validation
command and its actual result, including failures and skipped checks.
