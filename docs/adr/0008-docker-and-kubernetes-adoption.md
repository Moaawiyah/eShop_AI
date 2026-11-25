# ADR-0008: Docker and Kubernetes Adoption Strategy

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-25 |
| Deciders | Project owner |
| Jira | SHOP-003 |

## Context

Containers are needed for reproducible environments, CI parity and
deployment. Introducing everything at once would delay feature work;
introducing containers late would hide packaging problems until M7.
Kubernetes is a portfolio objective, but managed Kubernetes is the most
expensive cloud option.

## Decision

Adopt containers **progressively**:

| Stage | Milestone | Scope |
|---|---|---|
| Basic containers | M1 (SHOP-122) | Basic Dockerfiles for backend and frontend; Compose runs both |
| Progressive Compose | M2–M5 | PostgreSQL (M2), Redis (M3), worker (M5) added to Compose |
| Production optimization | M7 (SHOP-075, SHOP-076, SHOP-079) | Hardened multi-stage images, minimal bases, non-root, Trivy scanning, full-stack verification |
| Local Kubernetes | M8 | kind, Helm charts, Argo CD, observability |
| Cloud | M9–M10 | Platform per UD-01; Kubernetes in AWS only if the cost evaluation selects it |

- Native (non-container) development remains supported throughout.
- Images are built once and promoted by digest (ARCHITECTURE section 10.3).
- Local ports bind to `127.0.0.1`; secrets come from git-ignored `.env`.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Containers only in M7 | Packaging problems discovered late; CI parity delayed |
| Production-grade images in M1 | Premature optimization before the stack exists |
| Kubernetes from M1 | Slows feature work; high learning and maintenance cost early |
| EKS for all Kubernetes work | High fixed cost; kind provides the same Helm and GitOps practice locally |

## Consequences

**Positive**

- Early CI and local parity; incremental learning curve.
- Kubernetes skills demonstrated without cloud cost.

**Negative**

- Dockerfiles are revisited in M7.
- Developers maintain both native and container workflows.

## Related Requirements and Tasks

- Requirements: FR-DEV-001, FR-DEV-002, FR-DEV-007, FR-DEV-011, FR-DEV-013, NFR-PORT-001, NFR-SEC-018
- Tasks: SHOP-122, SHOP-022, SHOP-075, SHOP-076, SHOP-079
- Documents: ARCHITECTURE section 10; ROADMAP sections 2.4 and 5

## Reconsideration Conditions

Revisit the cloud part after the SHOP-093 cost evaluation; revisit the
Compose approach if local start-up exceeds 5 minutes or Compose drifts
from the Kubernetes configuration in ways that cause defects.
