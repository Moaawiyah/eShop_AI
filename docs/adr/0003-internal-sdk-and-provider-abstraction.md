# ADR-0003: Internal SDK and Provider Abstraction

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-25 |
| Deciders | Project owner |
| Jira | SHOP-003 |

## Context

The application will call several external systems: product data sources,
object storage, LLM providers, AWS, Jira and MCP. Most providers are not
yet chosen (UD-03, UD-06, UD-09, UD-10). Tests and local development must
run without accounts or cost, and provider failures must not leak into
business logic.

## Decision

Access every external system through an **internal SDK** in
`backend/app/integrations/`, organized by capability (`http`,
`product_data`, `storage`, `llm`, `aws`, `jira`, `mcp`).

- Each capability defines a typed interface; adapters implement it and
  are selected by configuration.
- Every interface has a deterministic mock, used by default locally and
  in tests.
- One shared HTTP client per application, created and closed by the
  composition root, with explicit timeouts.
- Adapters apply bounded retries, Gatekeeper quotas, idempotency keys,
  response validation and telemetry, and translate provider errors into a
  common integration error taxonomy.
- Official provider SDKs are used inside adapters where they exist;
  provider types never cross the interface.
- The SDK stays inside the backend until at least two independently
  deployed services need it.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Call provider SDKs directly from modules | Couples business logic to providers; hard to mock; inconsistent resilience |
| Generic third-party abstraction for all providers | Does not cover all capabilities; hides behaviour that must be controlled (budgets, retries) |
| Separate shared package now | Only one consumer exists; adds versioning overhead |

## Consequences

**Positive**

- Providers can be swapped or mocked without changing business logic.
- Resilience, quotas and telemetry are implemented once.
- Zero-cost local development and deterministic tests.

**Negative**

- Interface design effort before the first real provider exists.
- Risk of lowest-common-denominator interfaces; mitigated by keeping
  interfaces narrow and capability-specific.

## Related Requirements and Tasks

- Requirements: FR-PLAT-001, FR-PLAT-002, FR-PLAT-003, FR-PLAT-004, FR-PLAT-009, NFR-SEC-017, NFR-COST-006
- Tasks: SHOP-053, SHOP-054, SHOP-065
- Documents: ARCHITECTURE section 4

## Reconsideration Conditions

Revisit packaging when two or more independently deployed services need
the same integrations, or if an interface needs repeated provider-specific
exceptions (more than two per capability).
