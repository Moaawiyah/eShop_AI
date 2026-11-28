# eShop_AI — Development Guide

| Field | Value |
|---|---|
| Version | 0.1 — Draft |
| Jira | SHOP-004 (setup steps completed in SHOP-020) |
| Milestone | M1 — Frontend and Backend Foundations, Local Development and Basic CI |
| Last updated | 2026-11-25 |
| Related | [Architecture](ARCHITECTURE.md) · [Roadmap](ROADMAP.md) · [Security](SECURITY.md) · [Contributing](../CONTRIBUTING.md) |

> **Status:** the backend skeleton exists (SHOP-010); the frontend is
> **not initialized yet**. Only the commands marked **Available now** work
> today. Commands marked with a
> milestone become available when that milestone's tasks are done; their
> exact form is confirmed in the listed task.

## 1. Principles

- **Local first** ([ADR-0006](adr/0006-local-first-incremental-cloud.md)):
  every feature runs on a developer machine at zero cloud cost, using demo
  data and mock providers. No cloud account is needed.
- **One project, separate environments:** the backend and frontend each
  have their own isolated dependency environment; nothing is installed
  globally beyond the prerequisite tools.
- **Reproducible:** lockfiles are committed and CI installs from them.
- Engineering rules live in `CLAUDE.md` and `.claude/rules/`; this guide
  covers setup and daily workflow.

## 2. Prerequisites

| Tool | Version | Purpose | Needed from |
|---|---|---|---|
| macOS on Apple Silicon (primary); Linux or Windows with WSL 2 should work | Current | Development host | Now |
| Git | Recent | Version control | Now |
| Python | 3.11 or newer for repository scripts; **3.13** for the backend | Scripts now; backend from M1 | Now |
| [uv](https://docs.astral.sh/uv/) | Recent | Python versions, virtual environments, dependencies | M1 (SHOP-010) |
| Node.js | The Active LTS release when the frontend is created, pinned in `.nvmrc` and `engines` | Frontend | M1 (SHOP-014) |
| npm | Bundled with Node.js | Frontend dependencies | M1 |
| Docker Engine with Compose v2 (Docker Desktop or a compatible runtime) | Recent | Containers and local services | M1 (SHOP-122) |
| VS Code | Recent | Recommended editor (section 4) | Optional |
| kind, kubectl, Helm | Recent | Local Kubernetes | M8 |
| Terraform | Pinned in `infrastructure/` | Infrastructure as code (offline checks only without approval) | M9 |

Check the Node.js release schedule at
<https://nodejs.org/en/about/previous-releases> before pinning a version.

### 2.1 Apple Silicon Notes

- Use native arm64 builds of Python, Node.js and Docker.
- Prefer multi-architecture base images (`linux/arm64` and
  `linux/amd64`). If an image is amd64-only, emulation works but is slow;
  record such cases in the pull request.
- CI runs on `linux/amd64`; images are built for the CI platform there.
- Keep Docker's memory allocation at 4 GB or more once PostgreSQL, Redis
  and the applications run together.

## 3. Repository Layout

See `CLAUDE.md` section 5 and [ARCHITECTURE section 3](ARCHITECTURE.md#3-backend-architecture).
Directories other than `docs/`, `scripts/` and `.claude/` are empty until
their milestone.

## 4. VS Code

The repository ships `.vscode/settings.json` and `.vscode/extensions.json`.

- VS Code suggests the recommended extensions when you open the folder;
  nothing is installed automatically.
- Settings are workspace-wide and contain no personal paths. Personal
  settings belong in your user settings, not in the repository (other
  files under `.vscode/` are git-ignored).
- After the backend exists (M1), select the interpreter
  `backend/.venv/bin/python` with *Python: Select Interpreter*.
- After the frontend exists (M1), choose *TypeScript: Select TypeScript
  Version → Use Workspace Version* to use the project's TypeScript.
- Ruff formats and lints Python; Prettier formats TypeScript, JSON, CSS
  and Markdown; ESLint fixes are applied on save in the frontend.

## 5. Environments and Dependencies

### 5.1 Python (backend, M1)

- uv manages the Python version, the virtual environment
  (`backend/.venv`, git-ignored) and dependencies.
- Add dependencies with `uv add <package>` (or `uv add --dev <package>`)
  from `backend/`; never use `pip install` in the project.
- `backend/uv.lock` is committed; CI runs `uv sync --locked`.
- `backend/.python-version` pins Python 3.13 (`requires-python` is
  `>=3.13,<3.14`). If it is missing, `uv python install 3.13` installs a
  uv-managed interpreter.
- Deactivate any other project's virtual environment first (`deactivate`
  or `unset VIRTUAL_ENV`). uv warns about a different active environment,
  ignores it and uses `backend/.venv`.
- Settings are read from environment variables and the repository-root
  `.env` (copied from `.env.example`). Environment variables take
  precedence, and invalid values stop start-up.
- Every new dependency needs a justification (purpose, maintenance,
  license, alternatives) in the pull request.

### 5.2 Node.js (frontend, M1)

- `frontend/node_modules/` is local to the frontend and git-ignored.
- Add dependencies with `npm install <package>` (or `--save-dev`) from
  `frontend/`; `package-lock.json` is committed; CI runs `npm ci`.

### 5.3 Repository Scripts (now)

`scripts/` uses only the Python standard library and needs no virtual
environment. Run scripts with any Python 3.11+ interpreter, or through uv
without creating a project:

```bash
python3 scripts/validate_docs.py
uv run --no-project --python 3.13 scripts/validate_docs.py
```

## 6. Configuration and Environment Variables

- `.env.example` (committed) documents every planned variable with safe
  placeholders and the milestone in which it becomes supported.
- Create your local file with `cp .env.example .env` once an application
  reads it (M1). `.env` and `.env.*` are git-ignored, except examples.
- Replace placeholder secrets with generated values:
  `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
- Never commit `.env`, paste its contents into issues or prompts, or
  print secrets in logs.
- Defaults are safe: AI uses the mock provider, external sources and
  paid APIs are disabled.

Verify the ignore rules (**available now**):

```bash
git check-ignore -v .env .env.local      # both must be reported as ignored
git check-ignore -v .env.example          # must print nothing (exit code 1)
git ls-files .env.example                 # must list the file
```

## 7. Docker and Docker Compose

| Stage | Services | Milestone |
|---|---|---|
| Basic | `backend`, `frontend` | M1 (SHOP-122) |
| Data | + `postgres` | M2 (SHOP-022) |
| Sessions and limits | + `redis` | M3 (SHOP-030) |
| Jobs | + `worker`, optional mail catcher (UD-15) | M5 |
| Full stack | Profiles and one-command verification | M7 (SHOP-076) |
| Observability | Optional profile, or the kind cluster | M8 |

- All published ports bind to `127.0.0.1`.
- Data lives in named volumes. `docker compose down -v` **deletes local
  data**; use it only when you intend to reset.
- Native development (without containers) stays supported.

### 7.1 Planned Local Ports (Approved in SHOP-006)

| Service | Port | Milestone |
|---|---|---|
| Frontend (Next.js) | 3000 | M1 |
| Backend API (FastAPI) | 8000 | M1 |
| PostgreSQL | 5432 | M2 |
| Redis | 6379 | M3 |
| Mail catcher web UI | Decided with UD-15 | M5 (ADV) |
| Grafana | 3001 | M8 |
| Prometheus | 9090 | M8 |
| OpenTelemetry Collector (OTLP gRPC / HTTP) | 4317 / 4318 | M8 |
| Argo CD UI (port-forward) | 8080 | M8 |

If a port is in use, override it in `.env`; never change the defaults in
committed files for personal convenience.

## 8. Database Migrations and Seed Data

**Available from M2** (SHOP-023, SHOP-025).

- Schema changes are made only through Alembic migrations
  (`backend/migrations/`); never edit an applied migration.
- Migrations follow expand/contract so the previous release keeps working.
- CI verifies upgrade and downgrade.
- The demo seeder is deterministic (fixed seed) and creates synthetic
  data only; it is safe to re-run on a local database.
- Dropping or resetting a shared or cloud database is a destructive
  operation and requires explicit owner approval.

## 9. Command Reference

| Purpose | Command (run from) | Availability |
|---|---|---|
| Validate documentation | `python3 scripts/validate_docs.py` (root) | **Available now** |
| Validator and Claude hook self-tests | `python3 -m unittest discover -s scripts/tests` (root) | **Available now** |
| Check ignore rules | `git check-ignore -v .env` (root) | **Available now** |
| Validate JSON configuration | `python3 -m json.tool .vscode/settings.json` and `.claude/settings.json` (root) | **Available now** |
| Install backend dependencies | `uv sync --locked` (`backend/`; creates `backend/.venv`) | **Available now** |
| Run the backend | `uv run python -m app` (`backend/`; host, port and shutdown timeout from settings) | **Available now** |
| Run the backend with reload | `uv run uvicorn app.main:create_app --factory --reload` (`backend/`) | **Available now** |
| Open the API documentation | `http://127.0.0.1:8000/api/v1/docs` (OpenAPI: `/api/v1/openapi.json`; development and test only) | **Available now** |
| Probe liveness and readiness | `curl -i http://127.0.0.1:8000/health/live` and `curl -i http://127.0.0.1:8000/health/ready` (backend running; ready returns 503 before start-up and during shutdown) | **Available now** |
| Backend tests with coverage | `uv run pytest --cov=app --cov-branch --cov-report=term-missing` (`backend/`; plain `uv run pytest` also works) | **Available now** |
| Backend lint | `uv run ruff check .` (`backend/`; fix with `uv run ruff check --fix .`) | **Available now** |
| Backend format check | `uv run ruff format --check .` (`backend/`; fix with `uv run ruff format .`) | **Available now** |
| Backend type check | `uv run mypy app` (`backend/`) | **Available now** |
| Backend import contracts | `uv run lint-imports` (`backend/`; contracts in `pyproject.toml`) | **Available now** |
| Install frontend dependencies | `npm ci` (`frontend/`) | M1 (SHOP-014) |
| Run the frontend | `npm run dev` (`frontend/`) | M1 |
| Frontend lint, type check, build | `npm run lint`, `npm run typecheck`, `npm run build` (`frontend/`) | M1 |
| Generate API types | `npm run generate:api` (`frontend/`; generator per UD-14) | M1 (SHOP-015) |
| Start containers | `docker compose up --build` (root) | M1 (SHOP-122) |
| Stop containers | `docker compose down` (root) | M1 |
| Apply migrations | `uv run alembic upgrade head` (`backend/`) | M2 (SHOP-023) |
| Seed demo data | Seeder command defined in SHOP-025 (`backend/`) | M2 |
| End-to-end tests | Tool per UD-12 (SHOP-030) | M3 |
| AI evaluation suites | `tests/ai/` runner defined in SHOP-069 | M6 |
| Local Kubernetes | `kind create cluster`, Helm and Argo CD steps defined in M8 | M8 |

SHOP-020 replaces the M1 rows with the final, verified commands.

## 10. Testing, Linting and Type Checking

- Rules: `.claude/rules/testing.md`, `.claude/rules/backend.md`,
  `.claude/rules/frontend.md`.
- Run tests, linting and type checks locally before opening a pull
  request; CI runs the same commands (from M1, SHOP-017).
- Integration tests use PostgreSQL in Docker, not SQLite.
- Tests never call live external services; mocks are the default.
- Report only results you actually observed.

## 11. API Documentation and Frontend Types

**Available from M1** (SHOP-010, SHOP-015).

- FastAPI serves the OpenAPI document at `/api/v1/openapi.json` and
  interactive documentation locally (disabled or protected outside local
  development).
- Frontend types are generated from that document (generator chosen in
  SHOP-015, UD-14) and committed; CI fails when generated types are out of
  date. Never hand-write duplicate request or response types.

## 12. Debugging and Troubleshooting

| Symptom | Check |
|---|---|
| Port already in use | `lsof -nP -iTCP:<port> -sTCP:LISTEN`; stop the process or override the port in `.env` |
| Backend cannot reach PostgreSQL or Redis | `docker compose ps` and service health; host and port in `.env`; use service names inside Compose, `localhost` outside |
| Sign-in works but requests fail with 403 | Missing CSRF header or mismatched origin; check the browser's request headers |
| Session cookie not sent | Frontend and API must be reached through the same origin; `Secure` cookies need HTTPS outside local development |
| VS Code uses the wrong Python | Select `backend/.venv/bin/python` |
| Slow containers on Apple Silicon | An amd64-only image is being emulated; use a multi-architecture image |
| Generated API types are stale | Regenerate the types and commit them |
| Need request details | Every log line and error response has a correlation ID; search logs for it |

Debugging rules: never paste secrets, session IDs or `.env` contents into
issues, logs or AI prompts; use synthetic data for reproductions.

### 12.1 Backend Logging

Run from `backend/`:

```bash
LOG_LEVEL=DEBUG uv run python -m app        # verbose output
LOG_FORMAT=console uv run python -m app     # human-readable lines
curl -i -H 'X-Request-ID: my-test-request-01' http://127.0.0.1:8000/api/v1/docs
curl -i http://127.0.0.1:8000/health/live    # 200 {"status":"ok"}
curl -i http://127.0.0.1:8000/health/ready   # 200 {"status":"ready"}, 503 {"status":"not_ready"} otherwise
```

The response echoes `X-Request-ID` (invalid values are replaced by a
generated one); search the logs for it. Example JSON line:

```json
{"timestamp": "2026-11-28T12:55:21.787Z", "level": "INFO", "service": "eshop-backend", "logger": "app.api.access", "event": "request completed", "correlation_id": "my-test-request-01", "method": "GET", "route": "/api/v1/example/{id}", "status_code": 200, "duration_ms": 0.166}
```

## 13. Branch Workflow

Follow `CLAUDE.md` section 10 and [CONTRIBUTING.md](../CONTRIBUTING.md).

```bash
git switch main && git pull --ff-only
git switch -c docs/SHOP-004-security-dev-config
# work, run checks, commit with Conventional Commits
git push -u origin docs/SHOP-004-security-dev-config   # requires owner approval when AI-assisted
```

## 14. Local Development versus Cloud Environments

| Aspect | Local (development) | Cloud (staging, demo production) |
|---|---|---|
| Status | Approved; available from M1 | Deferred (UD-01); requires cost approval |
| Platform | Native processes or Docker Compose; kind from M8 | Platform chosen in SHOP-093 |
| Data | Deterministic demo seed | Demo seed only |
| AI | Mock provider | Mock by default; real provider only with approval and a token budget |
| Secrets | `.env` (git-ignored) | Managed secrets service |
| TLS and cookies | HTTP on localhost; `Secure` cookie flag off | HTTPS; `Secure` and `__Host-` cookies |
| Images | Built locally | Immutable images promoted by digest |
| Cost | Zero | Estimated and approved before creation; torn down when idle |
| Access | Developer only | Defined per environment; no direct manual changes (GitOps) |

Environment differences are configuration only; the same code and images
run everywhere ([ARCHITECTURE section 10](ARCHITECTURE.md#10-devops-architecture)).
