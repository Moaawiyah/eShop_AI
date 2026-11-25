---
name: review-changes
description: "Review the current eShop_AI diff against project rules: correctness, maintainability, security, architecture boundaries and product invariants, with prioritized findings and file references. Manual invocation only; read-only."
argument-hint: "[base ref, default: merge base with main]"
disable-model-invocation: true
---

# Review Changes

Review the changes against **$ARGUMENTS** (default: the merge base with
`main`, plus uncommitted changes). Do not modify files unless the user
explicitly asks for fixes after the review.

1. **Collect the diff** with `git status --short`, `git diff --stat` and
   `git diff <base>...HEAD` plus `git diff HEAD`. Read surrounding code only
   where needed to judge a change.
2. **Check against project standards** (do not restate them; apply them):
   - Correctness: logic errors, edge cases, error handling, transactions.
   - Product invariants (`CLAUDE.md` section 3): integer cents, USD,
     simulated payments, availability categories only.
   - Architecture: module boundaries and ADRs in `docs/adr/`, internal SDK
     for external access, no unapproved dependencies or services.
   - Security: `.claude/rules/security.md` checklist; secrets in the diff.
   - Tests: success and failure paths; no weakened or deleted tests.
   - Maintainability: naming, duplication, file size (~150 lines guideline).
   - Documentation updated where behaviour or structure changed.
3. **Escalate only when justified.** For authentication, authorization,
   secrets, payments, AI tools or infrastructure changes, offer to run the
   `security-reviewer` agent; do not run it automatically.

## Output

Findings ordered **Critical, High, Medium, Low, Nit**, each with
`file:line`, the problem, why it matters and a concrete fix. Then list what
was not reviewed and a one-line verdict (ready, ready after fixes, not ready).
This complements the generic `/code-review` plugin with project-specific rules.
