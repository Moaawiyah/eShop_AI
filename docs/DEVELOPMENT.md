# eShop_AI — Development Guide

| Field | Value |
|---|---|
| Version | 0.2 |
| Jira | SHOP-004; setup and verification commands completed in SHOP-020 |
| Milestone | M1 — Frontend and Backend Foundations, Local Development and Basic CI |
| Last updated | 2026-11-28 |
| Related | [Architecture](ARCHITECTURE.md) · [Roadmap](ROADMAP.md) · [Security](SECURITY.md) · [Contributing](../CONTRIBUTING.md) |

> **Status:** the backend, the frontend and the basic Docker Compose stack
> exist (M1). A new contributor can clone, set up, run both applications and
> run every check using this guide alone. Commands marked **Available now**
> were verified; commands marked with a milestone become available when that
> milestone's tasks are done.

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
| [uv](https://docs.astral.sh/uv/) | Recent | Installs Python 3.13, creates `backend/.venv`, installs locked dependencies | Now |
| Python | 3.13 (installed by uv; `.python-version`); 3.11+ for `scripts/` | Backend and repository scripts | Now |
| Node.js | 26 LTS (`frontend/.nvmrc`, `engines` `>=26 <27`); use nvm or fnm | Frontend | Now |
| npm | Bundled with Node.js | Frontend dependencies | Now |
| Docker Desktop (Compose v2.24 or newer, needed for the optional `env_file`) | Recent | Compose stack; optional local Gitleaks | Now (optional for native work) |
| VS Code | Recent | Recommended editor (section 4) | Optional |
| kind, kubectl, Helm | Recent | Local Kubernetes | M8 |
| Terraform | Pinned in `infrastructure/` | Infrastructure as code (offline checks only without approval) | M9 |

Install commands (macOS; see each tool's site for Linux and WSL):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # or: brew install uv
brew install nvm                                    # or fnm; then: nvm install 26
# Docker Desktop: https://www.docker.com/products/docker-desktop/
```

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

### 2.2 Quick Start (first 15 minutes)

Native run (**available now**):

```bash
git clone https://github.com/Moaawiyah/eShop_AI.git && cd eShop_AI
cp .env.example .env                  # optional: defaults work without it

# Terminal 1: backend (http://127.0.0.1:8000)
cd backend && unset VIRTUAL_ENV
uv sync --locked                      # installs Python 3.13 and locked dependencies
uv run python -m app

# Terminal 2: frontend (http://127.0.0.1:3000)
cd frontend
nvm use                               # Node.js 26 (or: fnm use)
npm ci
npm run dev
```

Open <http://127.0.0.1:3000> and <http://127.0.0.1:3000/status> (shows
"Backend ready" when both apps run). Backend API documentation:
<http://127.0.0.1:8000/api/v1/docs>.

Docker alternative (**available now**; needs network for the image build):

```bash
docker compose up --build -d          # then open http://127.0.0.1:3000/status
docker compose ps                     # both services should become healthy
docker compose down                   # stop
```

Next: run every check once ([section 10.1](#101-run-all-checks-locally)).

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

### 5.1 Python (backend)

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

### 5.2 Node.js (frontend)

- Node.js 26 (Active LTS) is pinned in `frontend/.nvmrc` and the
  `engines` field of `frontend/package.json` (`>=26 <27`); with nvm run
  `nvm use` from `frontend/`.
- Install exactly the locked dependencies with `npm ci` from `frontend/`.
  `frontend/node_modules/` and `.next/` are local and git-ignored.
- Add dependencies with `npm install <package>` (or `--save-dev`) from
  `frontend/`; `package-lock.json` is committed; CI runs `npm ci`.

### 5.3 Repository Scripts

`scripts/` uses only the Python standard library and needs no virtual
environment. Run scripts with any Python 3.11+ interpreter, or through uv
without creating a project:

```bash
python3 scripts/validate_docs.py
uv run --no-project --python 3.13 scripts/validate_docs.py
```

### 5.4 Running Natively

| Item | Backend | Frontend |
|---|---|---|
| Start | `uv run python -m app` (`backend/`) | `npm run dev` (`frontend/`) |
| Default address | `127.0.0.1:8000` (`BACKEND_HOST`, `BACKEND_PORT`) | `localhost:3000` (`PORT=3001 npm run dev` changes it) |
| Reload on change | `uv run uvicorn app.main:create_app --factory --reload` | Built in (`next dev`) |
| Backend URL | n/a | `BACKEND_INTERNAL_URL`, read at runtime by the Next.js server; default `http://127.0.0.1:8000` |
| Logs | `LOG_FORMAT=console` for readable lines (default `json`), `LOG_LEVEL=DEBUG` | Terminal output |

- `ALLOWED_ORIGINS` (comma-separated, bare origins, no path or `*`) controls
  CORS and the `Origin` check on unsafe methods. Default when unset:
  `http://localhost:3000,http://127.0.0.1:3000`. Outside development
  (`APP_ENV=staging` or `production`) every origin must use `https://`.
  Add an origin only if you serve the frontend on another host or port.
- Feature flags are described in section 6; restart the backend after a
  change.
- The frontend proxies `/api/v1/*` to the backend, so the browser only talks
  to the frontend origin.

## 6. Configuration and Environment Variables

- `.env.example` (committed) documents every planned variable with safe
  placeholders and the milestone in which it becomes supported.
- Create your local file with `cp .env.example .env`; it is optional because
  every supported setting has a safe default. The backend reads it (repository
  root); the frontend never does (set `BACKEND_INTERNAL_URL` in
  the shell if needed). `.env` and `.env.*` are git-ignored, except examples.
- Supported variables today: `APP_ENV`, `APP_DEBUG`, `BACKEND_HOST`,
  `BACKEND_PORT`, `ALLOWED_ORIGINS`, `SHUTDOWN_TIMEOUT_SECONDS`, `LOG_LEVEL`,
  `LOG_FORMAT`, `FEATURE_*`, `BACKEND_INTERNAL_URL` (frontend) and
  `FRONTEND_PORT` (Compose). All others in `.env.example` are planned.
- Replace placeholder secrets with generated values:
  `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
- Never commit `.env`, paste its contents into issues or prompts, or
  print secrets in logs.
- Defaults are safe: AI uses the mock provider, external sources and
  paid APIs are disabled.

Feature flags (SHOP-016, ADR-0009) are read from `FEATURE_AI_ASSISTANT`,
`FEATURE_EXTERNAL_PRODUCT_SOURCES` and `FEATURE_NOTIFICATIONS`; all default
to `false` and an invalid value stops start-up. Only `ai_assistant` is
public; read it with
`curl -s http://127.0.0.1:8000/api/v1/config/public-flags`
(`{"ai_assistant":false}`). Restart the backend after changing a flag.

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

**Basic stage — implemented (SHOP-122).** `compose.yaml` (repository root) runs:

- `backend` (`eshop-ai-backend:local`, port 8000) and `frontend`
  (`eshop-ai-frontend:local`, port 3000). The frontend starts after the backend
  is healthy and reaches it at `http://backend:8000` (`BACKEND_INTERNAL_URL`,
  set at runtime by Compose, never at build time).
- The Dockerfiles and `.dockerignore` files live next to each app
  (`backend/Dockerfile`, `frontend/Dockerfile`; build context is the app
  directory). `deployment/docker/` stays reserved for later stages.
- Health checks are defined in the Dockerfiles (backend `/health/ready`,
  frontend `/`). `docker compose ps` shows `starting`, then `healthy`; the
  frontend waits for a healthy backend, so it may take up to a minute.
- `.env` is optional: the backend reads it when present, the frontend never
  does. Compose forces `BACKEND_HOST=0.0.0.0` and `BACKEND_PORT=8000` inside the
  container; override only the published host ports with `BACKEND_PORT` and
  `FRONTEND_PORT` in `.env`.
- Containers run as non-root with a read-only root file system, `/tmp` as
  tmpfs, all capabilities dropped and `no-new-privileges`.
- The frontend build downloads fonts (`next/font/google`), so
  `docker compose build` needs network access.
- Images are basic (pinned tags, no digest pins, no scanning); production
  hardening is M7 (SHOP-075).

```bash
docker compose up --build -d   # build and start in the background
docker compose ps              # state and health
docker compose logs -f         # follow logs
docker compose logs backend    # logs of one service (also: frontend)
docker compose down            # stop and remove containers (no volumes yet)
```

Port override (host ports only; the apps still listen on 8000 and 3000
inside the containers):

```bash
BACKEND_PORT=8010 FRONTEND_PORT=3010 docker compose up --build -d
# or put BACKEND_PORT and FRONTEND_PORT in .env
docker inspect --format '{{json .State.Health}}' "$(docker compose ps -q backend)"
```

- All published ports bind to `127.0.0.1`.
- Data lives in named volumes (from M2). `docker compose down -v` **deletes local
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
| Validate documentation | `python3 scripts/validate_docs.py --strict` (root) | **Available now** |
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
| Install frontend dependencies | `npm ci` (`frontend/`) | **Available now** |
| Run the frontend | `npm run dev` (`frontend/`; http://127.0.0.1:3000, status page `/status`) | **Available now** |
| Frontend lint | `npm run lint` (`frontend/`; ESLint, zero warnings allowed) | **Available now** |
| Frontend format | `npm run format:check` / `npm run format` (`frontend/`; Prettier) | **Available now** |
| Frontend type check | `npm run typecheck` (`frontend/`) | **Available now** |
| Frontend tests | `npm test` (`frontend/`; Vitest) | **Available now** |
| Frontend production build | `npm run build` (`frontend/`; standalone output) | **Available now** |
| Generate API types | `npm run generate:api` (`frontend/`; needs `uv` and `uv sync --locked` in `backend/`) | **Available now** |
| Check API types for drift | `npm run check:api` (`frontend/`; fails when generated files are stale) | **Available now** |
| Start containers | `docker compose up --build -d` (root) | **Available now** |
| Container state and logs | `docker compose ps`, `docker compose logs backend` (root) | **Available now** |
| Stop containers | `docker compose down` (root) | **Available now** |
| Validate Compose file | `docker compose config --quiet` (root) | **Available now** |
| Secret scan (Gitleaks) | `docker run --rm -v "$PWD:/repo" ghcr.io/gitleaks/gitleaks:v8.30.1 git /repo --config /repo/.gitleaks.toml --redact` (root; needs Docker; uses `.gitleaks.toml`) | **Available now** once `.gitleaks.toml` is merged |
| Python dependency audit | See [section 10.2](#102-security-checks) (`backend/`) | **Available now** |
| npm dependency audit | `npm audit --omit=dev` (`frontend/`) | **Available now** |
| Apply migrations | `uv run alembic upgrade head` (`backend/`) | M2 (SHOP-023) |
| Seed demo data | Seeder command defined in SHOP-025 (`backend/`) | M2 |
| End-to-end tests | Tool per UD-12 (SHOP-030) | M3 |
| AI evaluation suites | `tests/ai/` runner defined in SHOP-069 | M6 |
| Local Kubernetes | `kind create cluster`, Helm and Argo CD steps defined in M8 | M8 |

## 10. Testing, Linting and Type Checking

- Rules: `.claude/rules/testing.md`, `.claude/rules/backend.md`,
  `.claude/rules/frontend.md`.
- Run the checks below before opening a pull request; CI runs the same
  commands.
- Integration tests use PostgreSQL in Docker, not SQLite (from M2).
- Tests never call live external services; mocks are the default.
- Report only results you actually observed.

### 10.1 Run All Checks Locally

This block mirrors the CI jobs (**available now**). Run it from the repository
root; each group stops at the first failure.

```bash
# Backend (CI job "Backend")
(cd backend && unset VIRTUAL_ENV && uv sync --locked \
  && uv run ruff check . \
  && uv run ruff format --check . \
  && uv run mypy app \
  && uv run lint-imports \
  && uv run pytest --cov=app --cov-branch --cov-report=term-missing)

# Frontend (CI job "Frontend")
(cd frontend && npm ci \
  && npm run lint \
  && npm run format:check \
  && npm run typecheck \
  && npm test \
  && npm run build)

# API types drift (CI job "API types drift"; needs the backend environment above)
(cd frontend && npm run check:api)

# Repository (CI job "Repository")
python3 scripts/validate_docs.py --strict
python3 -m unittest discover -s scripts/tests
```

### 10.2 Security Checks

```bash
# Gitleaks, full history (blocking in CI); needs Docker
docker run --rm -v "$PWD:/repo" ghcr.io/gitleaks/gitleaks:v8.30.1 \
  git /repo --config /repo/.gitleaks.toml --redact

# pip-audit (report only)
(cd backend && REQ="$(mktemp)" \
  && uv export --locked --no-dev --no-hashes --format requirements-txt > "$REQ" \
  && uvx pip-audit==2.10.1 -r "$REQ" --no-deps --disable-pip; rm -f "$REQ")

# npm audit (report only)
(cd frontend && npm audit --omit=dev)
```

Dependabot proposes grouped weekly updates for uv, npm, Docker and GitHub
Actions (`.github/dependabot.yml`); review them like any other change.

### 10.3 Continuous Integration

| Workflow | Job | Blocks merge | Runs |
|---|---|---|---|
| `ci.yml` | `Backend`, `Frontend`, `API types drift`, `Repository` | Through the aggregate `CI result` (required) | Pull requests and pushes to `main` |
| `security.yml` | `Gitleaks` | Yes (required) | Pull requests, pushes to `main`, weekly (Monday 06:00 UTC) and manual |
| `security.yml` | `pip-audit (report)`, `npm audit (report)` | No; reporting only until M7 adds gates | Same as Gitleaks |

- Branch protection on `main` requires `CI result` and `Gitleaks`.
- Results: the pull request's *Checks* tab, or the repository's *Actions*
  tab. Rerun a failed job with *Re-run failed jobs*, or push a new commit.
- On pull requests a job runs only when its paths changed: `Backend` for
  `backend/**`, `Frontend` for `frontend/**`, `API types drift` for either,
  and all three when `ci.yml` itself changes; `Repository` always runs.
  `CI result` always reports and treats skipped jobs as passed, failed or
  cancelled jobs as failed. Every job runs on pushes to `main`.
- The CI target is under 10 minutes; dependency caches are used for uv and
  npm.
- Reproduce a failure locally with the matching command in section 10.1.

## 11. API Documentation and Frontend Types

**Available now** (SHOP-010, SHOP-015, SHOP-017).

- FastAPI serves the OpenAPI document at `/api/v1/openapi.json` and
  interactive documentation locally (disabled or protected outside local
  development).
- Frontend types are generated from that document (openapi-typescript,
  ADR-0010) and committed. `npm run generate:api` (`frontend/`) exports the
  document with `backend/scripts/export_openapi.py` and regenerates
  `src/lib/api/schema.d.ts`; `npm run check:api` fails when the committed
  files are stale (CI job `API types drift`). Both need `uv` and the backend
  environment (`uv sync --locked` in `backend/`); run `unset VIRTUAL_ENV`
  first if another virtual environment is active. Never hand-write
  duplicate request or response types.
- Regenerate whenever a backend route, request or response schema changes,
  and commit **both** generated files (`src/lib/api/openapi.json` and
  `src/lib/api/schema.d.ts`) with the change that caused it.
- Run both servers natively as in section 2.2 and open
  <http://127.0.0.1:3000/status>. The frontend reads `BACKEND_INTERNAL_URL`
  at runtime (default `http://127.0.0.1:8000`) and proxies `/api/v1/*` to it.

## 12. Debugging and Troubleshooting

| Symptom | Check |
|---|---|
| Port 3000 or 8000 already in use | `lsof -nP -iTCP:8000 -sTCP:LISTEN` (or `:3000`); stop the process, or override: `BACKEND_PORT=8010 uv run python -m app`, `PORT=3010 npm run dev`, and for Compose `BACKEND_PORT` or `FRONTEND_PORT` in `.env` |
| uv warns that `VIRTUAL_ENV` does not match the project environment | Another virtual environment is active; run `deactivate` or `unset VIRTUAL_ENV`, then repeat the command (uv uses `backend/.venv`) |
| `ValidationError` when the backend starts | An environment or `.env` value is invalid; the message names the setting. Typical causes: `ALLOWED_ORIGINS` with a path, `*` or `http://` while `APP_ENV` is `staging` or `production`; a non-boolean feature flag; unsupported `LOG_FORMAT` |
| Frontend `/status` shows "Backend unreachable" | The backend is not running or `BACKEND_INTERNAL_URL` points elsewhere; check `curl http://127.0.0.1:8000/health/ready`. In Compose the value is `http://backend:8000` and is set for you |
| 403 `origin_not_allowed` on a POST, PUT, PATCH or DELETE | The browser `Origin` is not in `ALLOWED_ORIGINS`; add the exact origin (scheme, host, port) and restart the backend |
| `npm run check:api` reports stale types | Run `npm run generate:api` in `frontend/` and commit `openapi.json` and `schema.d.ts`; if it cannot run, see the `VIRTUAL_ENV` row and run `uv sync --locked` in `backend/` |
| `docker compose build` fails while fetching fonts | The frontend build downloads Google fonts; check network, proxy and VPN, then rebuild |
| A container is `unhealthy` or restarting | `docker compose logs backend` (or `frontend`); `docker inspect --format '{{json .State.Health}}' "$(docker compose ps -q backend)"`; the startup `ValidationError` row also applies |
| `npm ci` or `npm run dev` refuses to run (`EBADENGINE`) | Node.js is not 26.x; run `nvm use` (or `fnm use`) in `frontend/` and check `node --version` |
| Gitleaks reports a finding | Treat it as a leak: rotate or revoke the secret, remove it from the code, and ask the owner how to handle history. Add an allow-list entry only for a verified false positive, never for a real secret |
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
