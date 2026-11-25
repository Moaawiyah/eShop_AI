---
name: prepare-commit
description: "Prepare an eShop_AI commit: inspect working tree and staged changes, flag unrelated files and potential secrets, confirm required validation ran, and propose a Conventional Commit message. Manual invocation only; never stages, commits or pushes."
argument-hint: "[SHOP-NNN]"
disable-model-invocation: true
---

# Prepare a Commit

Task: **$ARGUMENTS** (infer from the branch name if omitted).

1. **Inspect** with `git branch --show-current`, `git status --short`,
   `git diff --stat`, `git diff --cached --stat` and the relevant diffs.
   Warn if the branch is `main` or does not match
   `<prefix>/SHOP-NNN-<short-name>` (`CLAUDE.md` section 10).
2. **Group files** into: belongs to this task, unrelated, and generated or
   local (caches, editor files). Unrelated changes are reported, never
   silently included or discarded.
3. **Check for secrets** without printing values: file names matching
   secret patterns, `git check-ignore -v` for local files, and
   credential-shaped strings in the diff. Report the file and the kind of
   finding only.
4. **Confirm validation.** List the checks executed in this session with
   their results; if required checks have not run, say so and suggest
   `/validate-project`.
5. **Draft the message** in Conventional Commits form with the Jira key,
   for example `docs(SHOP-124): add project skills and subagents`, plus a
   short body explaining why.

## Output

Branch status, file groups, secret check result, validation status, the
exact `git add <files>` and `git commit` commands for the owner to run or
approve, and the proposed message. Do not run them.
