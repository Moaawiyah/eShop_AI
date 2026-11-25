---
name: validate-project
description: "Run the eShop_AI validation commands that are actually available (documentation validator, self-tests, and later lint, type checks and tests) for the whole project or one component, and report passed, failed and unavailable checks. Use before a commit or after a change."
argument-hint: "[all | docs | backend | frontend | infra]"
model: haiku
---

# Validate the Project

Scope: **$ARGUMENTS** (default `all`).

1. **Detect components.** A component is present only if its manifest exists:
   `backend/pyproject.toml`, `frontend/package.json`, `infrastructure/terraform/*.tf`,
   `deployment/helm/*/Chart.yaml`. Documentation checks are always present.
2. **Select commands** from `docs/DEVELOPMENT.md` section 9 (SHOP-020
   replaces the planned rows with final commands), using only rows marked
   available or whose component now exists:
   - docs: `python3 scripts/validate_docs.py --strict` and
     `python3 -m unittest discover -s scripts/tests -v`
   - backend (`backend/`): `uv run ruff check .`, `uv run ruff format --check .`,
     `uv run mypy .`, `uv run pytest`
   - frontend (`frontend/`): `npm run lint`, `npm run typecheck`, `npm run build`,
     and the test script once SHOP-020 defines it
   - infra (from M8 and M9): `terraform fmt -check -recursive`,
     `terraform validate`, `helm lint` (`.claude/rules/testing.md`)
3. **Check tools** with `command -v <tool>` before running. If a tool or
   environment is missing, mark the check **unavailable**; never install
   tools or dependencies and never run `uv sync` or `npm install`.
4. **Run** each selected command once from the correct directory. Do not
   change files to make a check pass.

## Output

| Check | Command | Result |
|---|---|---|

Result is one of **passed**, **failed** (with the first relevant error
lines), or **unavailable** (with the reason). Finish with one line: all
selected checks passed, or the number failed and unavailable. Never report
an unexecuted check as passed.
