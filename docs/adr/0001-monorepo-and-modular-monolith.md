# ADR-0001: Monorepo and Modular Monolith

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-25 |
| Deciders | Project owner |
| Jira | SHOP-003 |

## Context

eShop_AI is built by one developer with AI assistance. It needs clear
domain boundaries to demonstrate good design, but every additional
deployable unit adds CI, networking, observability and cost overhead.
Frontend, backend, infrastructure and deployment artefacts change together
in most tasks.

## Decision

Use **one Git repository** for frontend, backend, infrastructure,
deployment, monitoring and documentation, and build the backend as a
**FastAPI modular monolith**.

- Backend packages `api`, `core`, `database`, `modules`, `integrations`
  and `platform` follow the dependency rules in ARCHITECTURE section 3.2.
- Domain modules (auth, users, catalog, inventory, cart, orders, payments,
  admin, ai) interact only through public service interfaces; the module
  call graph is acyclic (ARCHITECTURE section 2.3).
- Platform components live in `backend/app/platform/` and run in-process.
- A worker process (M5) reuses the same codebase; it is not a separate
  service.
- Import boundaries are checked automatically in CI.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Microservices from the start | High operational cost and complexity without a scaling or team need |
| Separate repositories per application | Cross-cutting changes need coordinated pull requests; harder to keep docs and code consistent |
| Unstructured monolith | No enforceable boundaries; weak demonstration of architecture skills |

## Consequences

**Positive**

- One build, one database transaction scope, simple local development.
- Boundaries are explicit and testable, so extraction remains possible.
- Atomic changes across frontend, backend and documentation.

**Negative**

- Boundaries depend on discipline and an import-contract check.
- The API and worker scale together until extraction is justified.
- CI must use path filters to avoid running every job on every change.

## Related Requirements and Tasks

- Requirements: NFR-MNT-001, NFR-MNT-002, FR-PLAT-016
- Tasks: SHOP-003, SHOP-010, SHOP-011, SHOP-052
- Documents: ARCHITECTURE sections 3 and 13

## Reconsideration Conditions

Revisit when any extraction condition in ARCHITECTURE section 13 is met
and measured, or if more than one team works on the backend in parallel.
