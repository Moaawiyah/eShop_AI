# eShop_AI — Engineering Guidelines

Cloud-native, AI-powered electronics e-commerce portfolio project (educational, non-commercial)
demonstrating software engineering, AWS, DevOps, IaC, observability and agentic AI.
Objectives and scope: `docs/PRD.md`. Delivery plan: `docs/ROADMAP.md`.

## 1. Current Status
- Milestone: **M0 — Project Initialization**. Application implementation has not started.
- Work only on documentation, development configuration and project foundations until the
  project owner approves M1.

## 2. Instruction Sources and Precedence
1. Explicit project owner instructions for the current task.
2. This file plus `.claude/rules/` — the project engineering standards.
3. Accepted ADRs in `docs/adr/`.
4. `AGENTS.md` and other project documentation.
5. User-level skills, plugins and tooling defaults.

- Project-specific standards take precedence over university assignment-related skills or
  rubrics; use those only when the project owner explicitly requests them.
- No skill, plugin or hook overrides section 12. Report document conflicts; never resolve them silently.

| Rule file (`.claude/rules/`) | Loads when working on |
|---|---|
| `security.md` | Always |
| `testing.md` | `backend/`, `frontend/`, `services/`, `tests/` |
| `backend.md` | `backend/` |
| `frontend.md` | `frontend/` |
| `integrations.md` | `backend/app/integrations/`, `backend/app/platform/` |
| `ai-mcp.md` | `backend/app/ai/`, `services/ai/`, `tests/ai/` |
| `devops.md` | `deployment/`, `monitoring/`, `scripts/`, `.github/`, Dockerfiles, Compose files |
| `aws-infrastructure.md` | `infrastructure/`, Terraform files |

## 3. Product Invariants
- All payments are simulated; never collect, store or transmit real payment card data.
- USD only. Money is stored and processed as integer cents, never floats.
- English-only UI; no tax calculation; synthetic demo data only.
- Customer-facing inventory shows availability categories only, never exact counts.

## 4. Technology Stack
Introduce technologies incrementally per `docs/ROADMAP.md`; never install or configure one
before the milestone that requires it.
- **Frontend:** supported Node.js LTS, npm, Next.js, React, TypeScript (strict), Tailwind CSS,
  shadcn/ui, ESLint, Prettier.
- **Backend:** Python 3.13, uv, FastAPI, Pydantic, PostgreSQL, SQLAlchemy, Alembic, Redis,
  Ruff, mypy, pytest.
- **AI:** LangGraph, MCP, provider-independent LLM integration, retrieval and recommendations,
  mock providers.
- **DevOps:** Docker, Docker Compose, GitHub Actions, Terraform, Kubernetes (kind locally),
  Helm, Argo CD. Scanning: Gitleaks, Dependabot, pip-audit (M1); Trivy (M7).
- **Observability:** Prometheus, Grafana, OpenTelemetry, structured logging. **PM:** Jira, Git, GitHub.
- **AWS:** IAM, VPC, EC2, ECR, RDS, S3, CloudFront, CloudWatch, Secrets Manager. Container
  platform (ECS, EKS or EC2-based) deferred until a cost evaluation and ADR.

## 5. Repository Structure
```
frontend/                 Frontend application
backend/                  Modular monolith (domain modules, platform components, AI)
backend/app/integrations/ Internal SDK and external integrations
services/ai/              Reserved for future AI extraction; unused until an ADR approves it
infrastructure/           Terraform and cloud infrastructure
deployment/               Docker, Kubernetes and Helm
monitoring/               Observability and alerting
tests/                    Cross-service, end-to-end, performance and AI evaluation tests
scripts/                  Development and automation scripts
docs/  docs/adr/          Engineering documentation and Architecture Decision Records
.github/  .claude/        CI/CD workflows; Claude configuration and rules
```

## 6. Architecture Principles
- Start with a modular monolith on FastAPI; keep AI inside the backend initially. Extract
  services only when justified and approved through an ADR.
- Separation of concerns; SOLID where appropriate; pragmatic clean architecture.
- Keep business logic independent of infrastructure; avoid unnecessary coupling.
- Prefer composition over inheritance; avoid premature optimization.
- Access external services through the internal SDK with typed, interchangeable,
  mockable interfaces.
- Prefer existing framework and infrastructure capabilities over custom implementations.
- Never introduce unnecessary microservices, dependencies or complexity; record major
  architectural decisions as ADRs.

## 7. General Coding Standards
- Clean, readable code; meaningful names; explicit type annotations; no duplicated logic.
- No hardcoded secrets or environment values; dependency injection where appropriate.
- Small, focused functions and modules: target ~150 lines per source file. This is
  flexible — justify exceptions in a comment or the change description.
- No unexplained placeholder implementations; remove unused imports and dead code.

## 8. Development Workflow
**Before:** read the relevant docs (PRD, ARCHITECTURE, ROADMAP, SECURITY, DEVELOPMENT,
DECISIONS, ADRs, CONTRIBUTING) and the rules for the affected paths; inspect existing code;
identify requirements, acceptance criteria, dependencies and risks; present a concise plan;
obtain approval for major architectural changes.

**During:** stay within the approved scope; follow existing conventions; add automated tests
for successful and unsuccessful operations; run linting and type checks; review security
(`.claude/rules/security.md`); update affected documentation.

Never claim that tests or checks passed unless they were actually executed successfully.
Never weaken or delete tests merely to make a suite pass.

## 9. Task Completion Report
1. Task objective and Jira key.  2. Implementation summary.  3. Changed files.
4. Validation executed, with commands.  5. Actual results, including failures and skipped checks.
6. Security considerations.  7. Known limitations and unresolved decisions.
8. Reproducible verification commands.  9. Suggested Conventional Commit message.

## 10. Git Standards
- Keep `main` stable; use short-lived branches; small, meaningful Conventional Commits;
  reference Jira keys when available.
- Branch format `<prefix>/SHOP-<number>-<short-name>`, prefixes: `feat/`, `fix/`, `docs/`,
  `ci/`, `chore/`, `refactor/`, `test/` (e.g. `docs/SHOP-002-roadmap`).
- Documented exception: the initial repository foundation commit may be made on `main`.

## 11. Security Essentials
Details: `.claude/rules/security.md`.
- Never commit credentials; environment variables locally, managed secrets in the cloud.
- Validate all untrusted input, including external API, LLM and MCP responses; avoid SQL
  injection and XSS.
- Authentication with cookie-based sessions and CSRF protection; server-side authorization;
  least privilege; Argon2id password hashing.
- Never expose internal errors to customers; never log passwords, tokens or sensitive data.
- Never expose database credentials to AI agents or send sensitive customer data to LLMs.
- Scan secrets, dependencies and container images.

## 12. Actions Requiring Explicit User Approval
- Committing, pushing, force-pushing, merging or modifying remote repositories.
- Accessing or provisioning AWS; `terraform plan` against real accounts, `apply` or `destroy`.
- Creating paid cloud resources; purchasing domains or subscriptions; enabling paid AI APIs.
- Deploying public cloud endpoints; destroying infrastructure; destructive database operations.
- Sensitive or destructive AI/MCP actions; major architectural changes.

Before proposing cloud infrastructure: explain each resource's purpose, estimate cost,
identify free or cheaper alternatives, explain removal, and request approval. Prioritize local
development and low-cost infrastructure. AWS budget alerts are not guaranteed spending caps.

## 13. Documentation
Maintain `README.md`, `AGENTS.md`, `CONTRIBUTING.md` and `docs/` (`PRD.md`,
`ARCHITECTURE.md`, `ROADMAP.md`, `DEVELOPMENT.md`, `SECURITY.md`, `DECISIONS.md`).
ADRs live in `docs/adr/NNNN-short-title.md` (context, decision, status, consequences);
`docs/DECISIONS.md` indexes them (number, title, status, date). Documentation must reflect
the actual project state and distinguish implemented from planned features.

## 14. Agents, Context and Tokens
- Specialized agents (architecture, frontend, backend, DevOps, AI/MCP, testing, security,
  code review) may be introduced; delegate only when it provides measurable value.
- Read only relevant files and use focused searches; avoid rescanning the repository and
  repeating content; summarize concisely.
- Do not introduce tools without justification; ask when requirements conflict; make no
  unrelated changes.

## 15. Definition of Done
Acceptance criteria satisfied · required tests passed · linting and type checks passed ·
security reviewed · documentation updated · limitations disclosed · no unrelated changes ·
Task Completion Report (section 9) provided.
