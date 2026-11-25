# Contributing to eShop_AI

eShop_AI is an educational, non-commercial portfolio project maintained by
its owner with AI-assisted development. This guide describes **how work
flows**; the authoritative engineering rules are in:

| Topic | Authoritative source |
|---|---|
| Engineering standards, approvals, Definition of Done, report format | [`CLAUDE.md`](CLAUDE.md) |
| Path-specific rules (backend, frontend, testing, DevOps, AWS, AI, integrations, security) | [`.claude/rules/`](.claude/rules/) |
| Instructions for non-Claude assistants | [`AGENTS.md`](AGENTS.md) |
| Requirements and scope | [`docs/PRD.md`](docs/PRD.md) |
| Tasks, tiers and milestones | [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| Architecture and decisions | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| Setup and commands | [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) |
| Security controls and reporting | [`docs/SECURITY.md`](docs/SECURITY.md) |

When these sources disagree, follow the precedence in `CLAUDE.md` section
2 and report the conflict instead of resolving it silently.

## 1. Jira Task Lifecycle

Every change belongs to a Jira task `SHOP-NNN` that exists in
`docs/ROADMAP.md` section 7.

| Status | Entry condition | Exit condition |
|---|---|---|
| To Do | Task imported from the roadmap | Dependencies done; scope and acceptance criteria clear |
| In Progress | Branch created | Pull request opened with checks run locally |
| In Review | Pull request open | Review approved and required checks green |
| Done | Merged to `main` | Task Completion Report attached (`CLAUDE.md` section 9) |
| Blocked | Waiting on a decision or dependency | Blocker resolved; return to the previous status |

- Scope changes are recorded in the roadmap before implementation (for
  example, a task merged into another or split).
- Unresolved decisions (`UD-nn`) are decided through an ADR before the
  dependent work starts.

## 2. Branches

- Format and prefixes: `CLAUDE.md` section 10
  (`<prefix>/SHOP-<number>-<short-name>`, e.g. `feat/SHOP-031-identity`).
- Branch from an up-to-date `main`; keep branches short-lived (ideally
  under a week). A branch may build on an unmerged branch only when its
  task depends on that work; say so in the pull request.
- One task per branch.

## 3. Commits

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(SHOP-NNN): <imperative summary in lower case>

Optional body explaining why, not what.
```

- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`,
  `build`, `perf`.
- Breaking changes use `!` after the type and a `BREAKING CHANGE:` footer.
- Keep commits small and focused; never mix unrelated changes.
- Never commit secrets, `.env` files, generated build output or personal
  editor settings.
- AI-assisted commits keep the co-author trailer provided by the tool.

## 4. Pull Requests

A pull request is ready for review when:

- [ ] The title follows Conventional Commits and includes the Jira key.
- [ ] The description links the Jira task and states scope and
      acceptance criteria.
- [ ] Tests for successful **and** unsuccessful paths are included.
- [ ] Linting, formatting, type checks and tests pass locally (commands in
      `docs/DEVELOPMENT.md`); results are reported as actually observed.
- [ ] `python3 scripts/validate_docs.py` passes when documentation changed.
- [ ] Documentation reflects the change; implemented and planned features
      are distinguished.
- [ ] Security checklist completed (section 9).
- [ ] New dependencies are justified (purpose, maintenance, license,
      alternatives).
- [ ] Known limitations and follow-up tasks are listed.
- [ ] The Task Completion Report (`CLAUDE.md` section 9) is attached or
      included.

A repository ruleset protects `main` (SHOP-008): changes arrive through pull requests,
and force pushes and deletion are blocked. No external approval is required
(solo project; the owner reviews every pull request). Required CI checks are
introduced in M1 (SHOP-017, SHOP-018) and enforced in M7 (SHOP-080).

## 5. Code Review

- The project owner reviews and approves **every** pull request, including
  AI-generated changes. Nothing is merged unreviewed.
- Authors self-review the full diff first.
- Reviewers check correctness, tests, security, adherence to the
  architecture and ADRs, readability and documentation.
- Optional automated review (for example the code-review plugin or the
  `pr-review-toolkit` agents) supplements but never replaces human review.
- Findings are resolved or explicitly deferred with a follow-up task.
- Merge with a squash or rebase merge that keeps a Conventional Commit
  message; delete the branch after merging.

## 6. Coding Standards

- General standards: `CLAUDE.md` section 7; stack-specific rules in
  `.claude/rules/backend.md` and `.claude/rules/frontend.md`.
- **File size:** target about 150 lines per source file. The guideline is
  flexible: a longer file is acceptable when splitting it would hurt
  cohesion (for example a generated file, a migration, a large but simple
  table of data, or a test module for one unit). Justify the exception in
  a comment at the top of the file or in the pull request. Documentation
  files are not subject to this guideline.
- Follow existing conventions before introducing new ones.

## 7. Testing and Coverage

- Rules: `.claude/rules/testing.md`.
- At least 80% line coverage for critical backend logic (authentication,
  pricing, cart, checkout, inventory, imports and Gatekeeper), enforced in
  CI from M7 (NFR-TST-001, SHOP-080).
- Every bug fix includes a regression test.
- Never weaken, skip or delete tests to make a suite pass.

## 8. Documentation

- Update affected documents in the same pull request (`CLAUDE.md`
  section 13).
- Record major architectural decisions as ADRs using
  [`docs/adr/template.md`](docs/adr/template.md) and index them in
  `docs/DECISIONS.md`.
- Keep documentation concise; reference the PRD by requirement ID rather
  than repeating it.

## 9. Security Review

Every pull request answers the checklist in `.claude/rules/security.md`
(input validation, server-side authorization, secret and personal-data
exposure, justified dependencies and network calls, AI/MCP rules). Report
vulnerabilities privately as described in
[`docs/SECURITY.md` section 21](docs/SECURITY.md#21-vulnerability-reporting).

## 10. AI-Assisted Development

AI assistants (Claude Code and others) are encouraged; the human remains
responsible for every change.

- The assistant follows `CLAUDE.md`, the scoped rules and `AGENTS.md`, and
  works only within the approved task scope.
- The assistant presents a plan for non-trivial work and asks before major
  architectural changes.
- The assistant reports only validation it actually ran, with commands and
  results.
- The developer reviews every line before committing, verifies claims by
  running the commands, and checks generated dependencies, licenses and
  security-sensitive code with extra care.
- Never share secrets, real personal data or `.env` contents with an
  assistant; use synthetic data.
- Plugins, skills and hooks never override `CLAUDE.md` section 12.
- Shared Claude Code permission rules and hooks live in `.claude/settings.json`
  and `.claude/hooks/` (SHOP-007). They are defense in depth, not a sandbox:
  approval prompts still require human judgment. Personal rules saved by
  "Yes, and don't ask again" go to the git-ignored
  `.claude/settings.local.json`; never use it to weaken the shared deny rules.
- Hooks stay deterministic and fast: no LLM or network calls, no commits,
  pushes or deployments, and no full test runs after each edit. Every hook
  change needs tests in `scripts/tests/test_claude_hooks.py`.

### 10.1 Task Workflow with Project Skills and Agents

Project skills live in `.claude/skills/` and subagents in `.claude/agents/`
(SHOP-124); `scripts/validate_docs.py` checks their configuration. A typical
task uses only the steps it needs:

1. Plan the task: `/plan-task SHOP-NNN`.
2. Obtain the owner's approval of the plan and of any `CLAUDE.md`
   section 12 action.
3. Implement: `/implement-task SHOP-NNN`.
4. Run targeted validation: `/validate-project <component>`.
5. Review when the change is large or risky: `/review-changes`, and the
   `security-reviewer` or `qa-engineer` agent for security-sensitive or
   high-risk work.
6. Prepare the commit: `/prepare-commit SHOP-NNN`.
7. Obtain approval before committing or pushing; the owner runs or approves
   the commands.
8. Update the task status in Jira and `docs/ROADMAP.md`.

One implementation agent is normally enough; independent reviewers are added
only when complexity or risk justifies them. `/milestone-review`,
`/security-audit` and `/create-adr` are used at milestone ends or when a
decision arises. Skills that change files or review broadly run only when
invoked manually.

## 11. Human Approval for Sensitive Operations

The actions listed in `CLAUDE.md` section 12 require **explicit approval
from the project owner** for each occurrence. They include committing,
pushing and merging; any AWS access, `terraform plan` against real
accounts, `apply` or `destroy`; creating paid resources or enabling paid
AI APIs; public deployments; destructive database operations; and
sensitive AI/MCP actions. Approval in one context does not extend to
another.

## 12. Definition of Done

`CLAUDE.md` section 15, plus the milestone-specific additions in
`docs/ROADMAP.md` section 6 and each milestone's exit criteria.
