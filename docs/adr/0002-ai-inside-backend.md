# ADR-0002: AI Inside the Backend Initially

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-25 |
| Deciders | Project owner |
| Jira | SHOP-003 |

## Context

The shopping assistant must ground answers in live catalog data, respect
the caller's permissions and stay within token budgets. A separate AI
service would need its own authentication, a catalog API or data copy,
and additional deployment and monitoring, before any measured need.

## Decision

Implement AI as the **`backend/app/modules/ai/` domain module** inside the
modular monolith, with LLM and MCP adapters in
`backend/app/integrations/`.

- The AI module calls catalog and inventory only through their public
  services; it has no database credentials and runs no SQL.
- MCP tools are read-only, schema-validated and executed in-process with
  the caller's permissions.
- LLM access goes through a provider-independent port; the deterministic
  mock is the default (ADR-0003).
- Gatekeeper enforces token budgets and request limits.
- The customer assistant and the future DevOps assistant are separate
  graphs with separate tool allow-lists and budgets.
- `services/ai/` stays unused until an ADR approves extraction.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Separate AI microservice | Duplicate authentication and catalog access; extra cost; no measured need |
| AI calls from the frontend | Exposes provider keys and bypasses server-side authorization and grounding |
| Direct database access for the agent | Violates least privilege and the security rules |

## Consequences

**Positive**

- Grounding and authorization reuse existing services and checks.
- No extra network hop, deployment or credential set.
- Deterministic mock makes CI evaluation reproducible.

**Negative**

- Slow or heavy AI requests share resources with the API.
- AI dependencies (LangGraph, MCP SDK) enlarge the backend image.

## Related Requirements and Tasks

- Requirements: FR-AI-001 to FR-AI-010, NFR-AI-010 to NFR-AI-017, NFR-COST-006, NFR-PRIV-002
- Tasks: SHOP-064, SHOP-065, SHOP-066, SHOP-067, SHOP-068, SHOP-069
- Documents: ARCHITECTURE section 9

## Reconsideration Conditions

Extract an AI service only when a condition in ARCHITECTURE section 13 is
met: AI load pushes API p95 latency beyond NFR-PERF targets in two
consecutive load tests despite limits and worker offloading, AI requires a
conflicting runtime or dependency set, or a security boundary requires
separate credentials.
