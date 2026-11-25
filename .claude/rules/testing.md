---
paths:
  - "backend/**"
  - "frontend/**"
  - "services/**"
  - "tests/**"
---

# Testing Rules

PRD references: NFR-TST, section 19 (acceptance criteria).

## Required Test Types (according to the task)
- Unit tests for business logic.
- Integration tests for persistence, workers and integrations.
- API tests for every endpoint, including authorization failures.
- End-to-end tests for customer and administrator workflows.
- Security tests (authorization sweeps, CSRF, rate limits, injection).
- AI evaluation and prompt-injection suites (mock provider).
- Infrastructure validation (Helm lint/template, Terraform validate).

## Principles
- Test both successful and unsuccessful operations.
- Target at least 80% coverage for critical backend business logic:
  authentication, pricing, cart, checkout, inventory, imports and Gatekeeper.
- Never weaken, skip or delete tests merely to make the suite pass.
- Never claim tests passed unless they were executed successfully.
- Tests must be deterministic: no live network calls, seeded data,
  controlled time and randomness.
- Use the mock or fake implementation of every external port (LLM, data
  sources, payment simulator, notifications) in automated tests.
- Run integration tests against PostgreSQL, not SQLite.
- Each integration adapter has contract tests based on recorded fixtures.
- Each bug fix includes a regression test.

## Layout
- `backend/tests/` — unit, integration and API tests (pytest).
- Frontend unit and component tests live with the frontend application.
- `tests/` — cross-service end-to-end, performance and AI evaluation suites.
- End-to-end and load-testing tools are selected by ADR (PRD UD-12).

## Performance Tests
- Follow the reference environment and workload in PRD section 14.1.
- Record hardware, commit SHA and dataset version with every result.
