# eShop_AI — Architecture Decision Index

Architecture Decision Records (ADRs) live in [`docs/adr/`](adr/). Use the
[template](adr/template.md) for new decisions.

## Accepted and Proposed ADRs

| Number | Title | Status | Date |
|---|---|---|---|
| [ADR-0001](adr/0001-monorepo-and-modular-monolith.md) | Monorepo and modular monolith | Accepted | 2026-11-25 |
| [ADR-0002](adr/0002-ai-inside-backend.md) | AI inside the backend initially | Accepted | 2026-11-25 |
| [ADR-0003](adr/0003-internal-sdk-and-provider-abstraction.md) | Internal SDK and provider abstraction | Accepted | 2026-11-25 |
| [ADR-0004](adr/0004-cookie-sessions-and-csrf.md) | Cookie-based sessions with CSRF protection | Accepted | 2026-11-25 |
| [ADR-0005](adr/0005-integer-cents-usd.md) | Money as integer cents in USD | Accepted | 2026-11-25 |
| [ADR-0006](adr/0006-local-first-incremental-cloud.md) | Local-first development and incremental cloud adoption | Accepted | 2026-11-25 |
| [ADR-0007](adr/0007-postgresql-primary-database.md) | PostgreSQL as the primary database | Accepted | 2026-11-25 |
| [ADR-0008](adr/0008-docker-and-kubernetes-adoption.md) | Docker and Kubernetes adoption strategy | Accepted | 2026-11-25 |

## Pending Decisions

Unresolved decisions are tracked in PRD section 20.3 and become ADRs when
they are made.

| PRD ID | Decision | Decided in |
|---|---|---|
| UD-01 | AWS container platform | SHOP-093 |
| UD-02 | Frontend hosting model | SHOP-093 |
| UD-03 | Authorized product data sources | SHOP-051 |
| UD-04 | Background job runner | SHOP-051 |
| UD-05 | Monthly AWS budget ceiling | Before cloud deployment |
| UD-06 | LLM providers and daily token budget | SHOP-064 |
| UD-07 | Search implementation | SHOP-021 |
| UD-08 | Session store | SHOP-030 |
| UD-09 | Object storage for images | SHOP-051 (local), SHOP-093 (cloud) |
| UD-10 | MCP transport and external exposure | SHOP-064 |
| UD-11 | Repository visibility | Public, verified 2026-11-25 (SHOP-006); recorded in SHOP-008 |
| UD-12 | Load-testing and end-to-end testing tools | SHOP-030 (end-to-end), M7 (load testing) |
| UD-13 | Feature flag implementation | SHOP-016 |
| UD-14 | OpenAPI-to-TypeScript generator | SHOP-015 |
| UD-15 | Local mail catcher | Before notification work |

## Process

1. Copy `adr/template.md` to `adr/NNNN-short-title.md` using the next free
   number.
2. Set the status to *Proposed* and add a row to the table above.
3. Major architectural changes require project owner approval
   (CLAUDE.md section 12) before the status becomes *Accepted*.
4. Accepted ADRs are not edited in substance; a new ADR supersedes them
   and both rows are updated.
