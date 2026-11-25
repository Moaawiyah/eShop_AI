# ADR-0006: Local-First Development and Incremental Cloud Adoption

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-25 |
| Deciders | Project owner |
| Jira | SHOP-003 |

## Context

The project is non-commercial and self-funded. AWS charges accrue
continuously for some resources (control planes, NAT gateways, load
balancers, public IPv4 addresses), and budget alerts are not spending
caps. The Tier 1 portfolio release must be demonstrable without any cloud
account.

## Decision

Develop and demonstrate **locally first**, and adopt cloud services
**incrementally, only after explicit approval**.

- Every feature runs locally at zero cloud cost with demo data and mock
  providers.
- The AWS container platform (ECS, EKS or EC2-based) is **deferred**
  until a cost evaluation and ADR (UD-01, SHOP-093).
- Each cloud proposal states purpose, estimated cost, cheaper
  alternatives and removal steps, and requires project owner approval.
- All cloud infrastructure is defined in Terraform; `plan` against real
  accounts, `apply` and `destroy` require approval.
- Environments are ephemeral and destroyable when idle; the same images
  run locally and in the cloud.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Cloud-first development | Continuous cost; slower feedback; risk of unapproved spend |
| Choose EKS now | Highest fixed cost; decision lacks a cost evaluation |
| No cloud at all | Loses the AWS portfolio objective |

## Consequences

**Positive**

- Predictable cost and fast local feedback.
- Cloud work is introduced with evidence and approval.

**Negative**

- Some cloud-specific issues are discovered late (M9–M10).
- Local and cloud behaviour can diverge; mitigated by identical images and
  configuration-only differences.

## Related Requirements and Tasks

- Requirements: NFR-COST-001 to NFR-COST-005, NFR-COST-010, NFR-PORT-001, FR-DEV-014
- Tasks: SHOP-093, SHOP-094
- Documents: ARCHITECTURE sections 10 and 11; ROADMAP section 8

## Reconsideration Conditions

Revisit when the cost evaluation in SHOP-093 is complete, or if the
project gains a sponsor or free credits that change the cost constraints.
